from dataclasses import dataclass
from functools import lru_cache
from logging import Logger

from koi_net.effector import Effector
from koi_net.processor.kobj_queue import KobjQueue
from koi_net.protocol.event import EventType
from rid_lib import RID
from rid_lib.types import SlackChannel, SlackMessage, SlackUser
from slack_bolt import App

from . import message_content
from .rid_types import Telescoped
from .slack_interface.functions import SlackFunctions
from .slack_interface.block_builder import BlockBuilder
from .config import SlackTelescopeNodeConfig
from .persistent import PersistentMessage, PersistentUser, create_link
from .consts import MessageStatus, UserStatus, ActionId
from .utils import retraction_time_elapsed


@dataclass
class Orchestrator:
    kobj_queue: KobjQueue
    effector: Effector
    config: SlackTelescopeNodeConfig
    log: Logger
    slack_app: App
    slack_functions: SlackFunctions
    block_builder: BlockBuilder
    
    # BROADCAST METHODS
    def create_broadcast(self, message):
        p_message = PersistentMessage(message)
        
        broadcast_channel = SlackChannel(
            team_id=self.config.telescope.team_id,
            channel_id=self.config.telescope.broadcast_channel_id
        )
        
        p_message.broadcast_interaction = self.slack_functions.create_msg(
            broadcast_channel,
            self.block_builder.broadcast_interaction_blocks(message)
        )
    
    def delete_broadcast(self, message: SlackMessage):
        p_message = PersistentMessage(message)
        
        self.slack_functions.delete_msg(p_message.broadcast_interaction, alt_text="_This message has been retracted._")
    
    
    # CONSENT METHODS
    def create_consent_interaction(self, message):
        p_message = PersistentMessage(message)
        p_user = PersistentUser(p_message.author)
        p_user.status = UserStatus.PENDING
            
        self.log.debug(f"Sent consent interaction to user <{p_message.author}>")
        
        self.slack_functions.create_msg(
            p_message.author,
            self.block_builder.consent_welcome_msg_blocks()
        )
        
        p_message.consent_interaction = self.slack_functions.create_msg(
            p_message.author,
            text="Requesting to observe your message",
            blocks=self.block_builder.consent_interaction_blocks(message)
        )
        
    def handle_consent_interaction(self, action_id, message):
        p_message = PersistentMessage(message)
        
        persistent_user = PersistentUser(p_message.author)
        persistent_user.status = action_id
        
        self.slack_functions.delete_msg(p_message.consent_interaction)
        
        self.log.debug(f"User <{p_message.author}> has set consent status to {action_id}")
        self.log.debug(f"Handling message queue of size {len(persistent_user.msg_queue)}")
        
        while persistent_user.msg_queue:
            prev_message = persistent_user.dequeue()
            p_prev_message = PersistentMessage(prev_message)
            
            if action_id == ActionId.OPT_OUT:
                self.log.info(f"Message <{prev_message}> rejected")
                p_prev_message.status = MessageStatus.REJECTED
            
            elif action_id == ActionId.OPT_IN:
                self.log.info(f"Message <{prev_message}> accepted")
                p_prev_message.status = MessageStatus.ACCEPTED
                self.create_retract_interaction(prev_message)
                self.create_broadcast(prev_message)
                
                self.effector.deref(Telescoped(prev_message), refresh_cache=True)
                
                # handle_new_message(prev_message)
            
            elif action_id == ActionId.OPT_IN_ANON:
                self.log.info(f"Message <{prev_message}> accepted (anonymous)")
                p_prev_message.status = MessageStatus.ACCEPTED_ANON
                self.create_retract_interaction(prev_message)
                self.create_broadcast(prev_message)
                
                self.effector.deref(Telescoped(prev_message), refresh_cache=True)
                
                # handle_new_message(prev_message)
                
            self.slack_functions.update_msg(p_message.request_interaction, self.block_builder.end_request_interaction_blocks(message))

    def slack_message_rid_to_url(self, rid: SlackMessage):
        @lru_cache(maxsize=128)
        def cached(rid: SlackMessage):
            url_str = self.slack_app.client.chat_getPermalink(
                channel=rid.channel_id,
                message_ts=rid.ts
            )["permalink"]
            return RID.from_string(url_str)
        return cached(rid)

    # REQUEST METHODS
    def create_request_interaction(
        self,
        message: SlackMessage, 
        author: SlackUser, 
        tagger: SlackUser
    ):
        p_message = PersistentMessage(message)
        
        # message previously been tagged and handled   
        if p_message.status != MessageStatus.UNSET:
            return
        
        p_message.status = MessageStatus.TAGGED
        p_message.author = author
        p_message.tagger = tagger
        p_message.permalink = self.slack_message_rid_to_url(message)
        
        author_data = self.effector.deref(author).contents
        author_name = author_data.get("real_name", f"<{author.user_id}>")
        tagger_name = self.effector.deref(tagger).contents.get(
            "real_name", f"<{tagger.user_id}>")
        
        channel_data = self.effector.deref(message.channel).contents
        self.log.debug(f"New message <{message}> tagged in #{channel_data['name']} "
            f"(author: {author_name}, tagger: {tagger_name})"
        )
        
        observatory_channel = SlackChannel(
            team_id=self.config.telescope.team_id,
            channel_id=self.config.telescope.observatory_channel_id
        )
        
        if message.channel.channel_id not in self.config.telescope.allowed_channels:
            self.log.debug("message not sent in allowed channel, ignoring")
            return
        
        if channel_data["is_archived"] == True:
            p_message.status = MessageStatus.UNREACHABLE
            
            self.slack_functions.create_msg(observatory_channel, text=f"The <{p_message.permalink}|message you just tagged> is located in an archived channel and cannot be observed.")
            self.log.debug("Message was unreachable")
            return
            
        if author_data["deleted"] == True:
            p_message.status = MessageStatus.UNREACHABLE
            
            self.slack_functions.create_msg(observatory_channel, text=f"The <{p_message.permalink}|message you just tagged> was authored by the deactivated account <@{author.user_id}> and cannot give consent.")
            self.log.debug("Message was authored by deleted user")
            return
        
        p_message.request_interaction = self.slack_functions.create_msg(
            observatory_channel,
            self.block_builder.request_interaction_blocks(message)
        )
        
        create_link(p_message.request_interaction, message)
        
    def handle_request_interaction(self, action_id, message):
        p_message = PersistentMessage(message)
        p_user = PersistentUser(p_message.author)
        author = self.effector.deref(p_message.author).contents
        
        self.log.debug(f"Handling request interaction action: '{action_id}' for message <{message}>")
        if action_id == ActionId.REQUEST:
            self.log.debug(f"User <{p_message.author}> status is: '{p_user.status}'")
            if p_user.status == UserStatus.UNSET:
                
                # bots can't consent, opt in by default
                if author["is_bot"]:
                    p_user.status = UserStatus.OPT_IN
                else:
                    self.create_consent_interaction(message)
                
            if p_user.status == UserStatus.PENDING:
                self.log.info(f"Queued message <{message}>")
                p_user.enqueue(message)
                p_message.status = MessageStatus.REQUESTED
                
            elif p_user.status == UserStatus.OPT_IN:
                self.log.info(f"Message <{message}> accepted")
                p_message.status = MessageStatus.ACCEPTED
                self.create_retract_interaction(message)
                self.create_broadcast(message)
                
                self.effector.deref(Telescoped(message))
                
                # handle_new_message(message)
                
            elif p_user.status == UserStatus.OPT_IN_ANON:
                self.log.info(f"Message <{message}> accepted (anonymous)")
                p_message.status = MessageStatus.ACCEPTED_ANON
                self.create_retract_interaction(message)
                self.create_broadcast(message)
                
                self.effector.deref(Telescoped(message))

                # handle_new_message(message)
                
            elif p_user.status == UserStatus.OPT_OUT:
                self.log.info(f"Message <{message}> rejected")
                p_message.status = MessageStatus.REJECTED
            
            self.slack_functions.update_msg(
                p_message.request_interaction, 
                self.block_builder.end_request_interaction_blocks(message)
            )
        
        elif action_id == ActionId.IGNORE:
            self.log.info(f"Message <{message}> ignored")
            p_message.status = MessageStatus.IGNORED
            
            self.slack_functions.update_msg(
                p_message.request_interaction,
                self.block_builder.alt_request_interaction_blocks(message)
            )
                
        elif action_id == ActionId.UNDO_IGNORE:
            self.log.info(f"Message <{message}> unignored")
            p_message.status = MessageStatus.TAGGED
            
            self.slack_functions.update_msg(
                p_message.request_interaction,
                self.block_builder.request_interaction_blocks(message)
            )

    # RETRACT METHODS
    def create_retract_interaction(self, message):
        p_message = PersistentMessage(message)
        
        p_message.retract_interaction = self.slack_functions.create_msg(
            p_message.author,
            text="Your message has been observed",
            blocks=self.block_builder.retract_interaction_blocks(message)
        )

    def handle_retract_interaction(self, action_id, message):
        p_message = PersistentMessage(message)
        
        if not retraction_time_elapsed(p_message):
            if action_id == ActionId.RETRACT:
                self.log.info(f"Message <{message}> retracted")
                p_message.status = MessageStatus.RETRACTED
            
                self.slack_functions.update_msg(
                    p_message.retract_interaction, 
                    self.block_builder.end_retract_interaction_blocks(
                        message, message_content.retract_success
                    )
                )
                
                self.delete_broadcast(message)
                
                self.kobj_queue.push(rid=Telescoped(message), event_type=EventType.FORGET)
                
                # handle_forget_message(message)
            
            elif action_id == ActionId.ANONYMIZE:
                self.log.info(f"Message <{message}> anonymized")
                p_message.status = MessageStatus.ACCEPTED_ANON

                self.slack_functions.update_msg(
                    p_message.retract_interaction, 
                    self.block_builder.end_retract_interaction_blocks(
                        message, message_content.anonymize_success
                    )
                )
                
                self.effector.deref(Telescoped(message), refresh_cache=True)
                
                # handle_update_message(message)
            
            self.slack_functions.update_msg(p_message.request_interaction, self.block_builder.end_request_interaction_blocks(message))
            
        else:
            self.log.info(f"Message <{message}> could not be retracted")
            self.slack_functions.update_msg(
                p_message.retract_interaction, 
                self.block_builder.end_retract_interaction_blocks(
                    message, message_content.retract_failure
                )
            )
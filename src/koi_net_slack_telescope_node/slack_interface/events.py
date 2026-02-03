from dataclasses import dataclass
from logging import Logger

from koi_net.effector import Effector
from rid_lib.types import SlackMessage, SlackUser
from slack_bolt import App

from ..config import SlackTelescopeNodeConfig
from ..persistent import PersistentMessage, get_linked_message
from ..consts import MessageStatus
from ..rid_types import Telescoped
from ..orchestrator import Orchestrator
# from ..orchestrator.message_handlers import handle_update_message


@dataclass
class SlackEventHandler:
    log: Logger
    slack_app: App
    config: SlackTelescopeNodeConfig
    effector: Effector
    orchestrator: Orchestrator
    
    def register_handlers(self):
        @self.slack_app.event("reaction_added")
        def handle_reaction_added(body, event):
            if event["item"]["type"] != "message":
                return
            
            team_id = body["team_id"]
            tagged_msg = SlackMessage(
                team_id, 
                event["item"]["channel"], 
                event["item"]["ts"]
            )
            emoji_str = event["reaction"]
            
            if event["item_user"] == self.config.telescope.bot_user_id:
                # only handle reqactions to interactions in the observatory
                if tagged_msg.channel_id != self.config.telescope.observatory_channel_id:
                    return
                
                original_message = get_linked_message(tagged_msg)
                if original_message is None: return
                
                self.log.debug(f"Adding '{emoji_str}' emoji to <{tagged_msg}>")
                p_msg = PersistentMessage(original_message)
                if p_msg.status != MessageStatus.UNSET:
                    p_msg.add_emoji(emoji_str)
                    
                    # acknowledge emoji
                    self.slack_app.client.reactions_add(
                        channel=tagged_msg.channel_id,
                        timestamp=tagged_msg.ts,
                        name=emoji_str
                    )
                    
                    # handle_update_message(p_msg.rid)
                    self.effector.deref(Telescoped(p_msg.rid), refresh_cache=True)
            
            elif emoji_str == self.config.telescope.emoji:
                self.log.debug("got a reaction")
                tagger = SlackUser(team_id, event["user"])
                author = SlackUser(team_id, event["item_user"])
                    
                self.orchestrator.create_request_interaction(tagged_msg, author, tagger)
                
        @self.slack_app.event("reaction_removed")
        def handle_reaction_removed(body, event):
            if event["item"]["type"] != "message":
                return

            tagged_msg = SlackMessage(
                body["team_id"], 
                event["item"]["channel"], 
                event["item"]["ts"]
            )
            emoji_str = event["reaction"]

            if event["item_user"] == self.config.telescope.bot_user_id:
                # only handle reqactions to interactions in the observatory
                if tagged_msg.channel_id != self.config.telescope.observatory_channel_id: return
                
                original_message = get_linked_message(tagged_msg)
                if original_message is None: return
                
                self.log.debug(f"Removing '{emoji_str}' emoji from <{tagged_msg}>")
                p_msg = PersistentMessage(original_message)
                if p_msg.status != MessageStatus.UNSET:
                    num_reactions = p_msg.remove_emoji(emoji_str)
                    
                    # remove acknowledgement if all emojis are removed
                    if num_reactions == 0:
                        self.slack_app.client.reactions_remove(
                            channel=tagged_msg.channel_id,
                            timestamp=tagged_msg.ts,
                            name=emoji_str
                        )
                    
                    # handle_update_message(p_msg.rid)
                    self.effector.deref(Telescoped(p_msg.rid), refresh_cache=True)
                    

        @self.slack_app.event({
            "type": "message",
            "channel": self.config.telescope.observatory_channel_id
        })
        def handle_message_reply(event):
            # only handle replies to bot message
            if event.get("parent_user_id") != self.config.telescope.bot_user_id:
                return
            
            replied_message = SlackMessage(
                event["team"],
                event["channel"],
                event["thread_ts"]
            )
                
            original_message = get_linked_message(replied_message)
            if original_message is None: return
            
            p_message = PersistentMessage(original_message)
            p_message.add_comment(event["text"])
            
            self.slack_app.client.reactions_add(
                channel=event["channel"],
                timestamp=event["ts"],
                name="thumbsup"
            )
            
            # handle_update_message(p_message.rid)
            self.effector.deref(Telescoped(p_message.rid), refresh_cache=True)
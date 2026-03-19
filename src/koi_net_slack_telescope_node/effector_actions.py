from dataclasses import dataclass
from logging import Logger

from koi_net.components.interfaces import DerefHandler
from slack_bolt import App
from slack_sdk.errors import SlackApiError
from rid_lib.ext import Bundle
from rid_lib.types import SlackMessage, SlackUser, SlackChannel, SlackWorkspace

from .rid_types import Telescoped
from .persistent import PersistentMessage
from .consts import MessageStatus
from . import utils


@dataclass
class DerefSlackUser(DerefHandler):
    slack_app: App
    
    rid_types=(SlackUser,)
    
    def handle(self, rid: SlackUser):
        return Bundle.generate(
            rid=rid,
            contents=self.slack_app.client.users_info(user=rid.user_id)["user"]
        )

@dataclass
class DerefSlackMessage(DerefHandler):
    log: Logger
    slack_app: App
    
    rid_types=(SlackMessage,)
    
    def join_and_retry_on_err(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SlackApiError as err:
            if err.response["error"] == "not_in_channel":
                self.log.debug(f"joining channel {kwargs['channel']}")
                try:
                    self.slack_app.client.conversations_join(
                        channel=kwargs["channel"]
                    )
                except SlackApiError as err:
                    if err.response["error"] == "is_archived":
                        self.log.warning("channel is archived, dereference failed")
                        return None
                    else:
                        raise err
                return func(*args, **kwargs)
            else:
                raise err
    
    def handle(self, rid: SlackMessage):
        resp = self.join_and_retry_on_err(
            func=self.slack_app.client.conversations_replies,
            channel=rid.channel_id,
            ts=rid.ts,
            limit=1
        )
        
        if not resp:
            return
        
        messages = resp["messages"]
        
        if len(messages) == 0:
            return
        
        return Bundle.generate(
            rid=rid,
            contents=messages[0]
        )

@dataclass
class DerefSlackChannel(DerefHandler):
    slack_app: App
    
    rid_types=(SlackChannel,)
    
    def handle(self, rid: SlackChannel):
        return Bundle.generate(
            rid=rid,
            contents=self.slack_app.client.conversations_info(
                channel=rid.channel_id
            )["channel"]
        )

@dataclass
class DerefSlackWorkspace(DerefHandler):
    slack_app: App
    
    rid_types=(SlackWorkspace,)

    def handle(self, rid: SlackWorkspace):
        return Bundle.generate(
            rid=rid,
            contents=self.slack_app.client.team_info(
                team=rid.team_id
            )["team"]
        )

@dataclass
class DerefTelescoped(DerefHandler):
    rid_types=(Telescoped,)

    def handle(self, rid: Telescoped):
        msg: SlackMessage = rid.wrapped_rid
        p_msg = PersistentMessage(msg)
        
        if p_msg.status not in (MessageStatus.ACCEPTED, MessageStatus.ACCEPTED_ANON):
            return
        
        message_bundle = self.effector.deref(msg)
        if not message_bundle:
            return
        
        message_data = message_bundle.contents
        channel_data = self.effector.deref(msg.channel).contents
        team_data = self.effector.deref(msg.workspace).contents
        author_data = self.effector.deref(p_msg.author).contents
        tagger_data = self.effector.deref(p_msg.tagger).contents
        
        message_in_thread = msg.ts != message_data.get("thread_ts", msg.ts)
        edited_timestamp = message_data.get("edited", {}).get("ts")
        edited_at = utils.format_timestamp(edited_timestamp) if edited_timestamp else None
        created_at = utils.format_timestamp(msg.ts)
        retract_time_started_at = utils.format_timestamp(p_msg.retract_interaction.ts)
        
        if p_msg.status == MessageStatus.ACCEPTED:
            author_user_id = p_msg.author.user_id
            author_name = author_data.get("real_name")
            anonymous = False
            
        elif p_msg.status == MessageStatus.ACCEPTED_ANON:
            author_user_id = None
            author_name = None
            anonymous = True
            
        # extract keys from emojis if num reactions > 0
        emojis = [
            k for k, v in p_msg.emojis.items()
            if v > 0
        ] if p_msg.emojis else []
        
        msg_url = str(p_msg.permalink)
            
        msg_json = {
            "message_rid": str(msg),
            "team_id": msg.team_id,
            "team_name": team_data["name"],
            "channel_id": msg.channel_id,
            "channel_name": channel_data["name"],
            "timestamp": msg.ts,
            "text": message_data.get("text", ""),
            "thread_timestamp": message_data.get("thread_ts"),
            "message_in_thread": message_in_thread,
            "created_at": created_at,
            "edited_at": edited_at,
            "author_user_id": author_user_id,
            "author_name": author_name,
            "tagger_user_id": p_msg.tagger.user_id,
            "tagger_name": tagger_data.get("real_name"),
            "author_is_anonymous": anonymous,
            "emojis": emojis,
            "comments": p_msg.comments or [],
            "retract_time_started_at": retract_time_started_at,
            "permalink": msg_url
        }
        
        return Bundle.generate(
            rid=rid,
            contents=msg_json
        )
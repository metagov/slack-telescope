import logging
from slack_sdk.errors import SlackApiError
from rid_lib.ext import Bundle
from rid_lib.types import SlackMessage, SlackUser, SlackChannel, SlackWorkspace
from koi_net.context import ActionContext
from .core import node, slack_app
from .rid_types import Telescoped
from .persistent import PersistentMessage
from .constants import MessageStatus
from . import utils

logger = logging.getLogger(__name__)


# DEREFERENCE

@node.effector.register_action(SlackUser)
def deref_slack_user(ctx: ActionContext, rid: SlackUser):
    return Bundle.generate(
        rid=rid,
        contents=slack_app.client.users_info(
            user=rid.user_id
        )["user"]
    )

@node.effector.register_action(SlackMessage)
def deref_slack_message(ctx: ActionContext, rid: SlackMessage):
    def join_and_retry_on_err(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SlackApiError as err:
            if err.response["error"] == "not_in_channel":
                logger.debug(f"joining channel {rid.channel_id}")
                slack_app.client.conversations_join(
                    channel=rid.channel_id
                )
                return func(*args, **kwargs)
            else:
                raise err

    return Bundle.generate(
        rid=rid,
        contents=join_and_retry_on_err(
            func=slack_app.client.conversations_replies,
            channel=rid.channel_id,
            ts=rid.ts,
            limit=1
        )["messages"][0]
    )

@node.effector.register_action(SlackChannel)
def deref_slack_channel(ctx: ActionContext, rid: SlackChannel):
    return Bundle.generate(
        rid=rid,
        contents=slack_app.client.conversations_info(
            channel=rid.channel_id
        )["channel"]
    )

@node.effector.register_action(SlackWorkspace)
def deref_slack_workspace(ctx: ActionContext, rid: SlackWorkspace):
    return Bundle.generate(
        rid=rid,
        contents=slack_app.client.team_info(
            team=rid.team_id
        )["team"]
    )
    
@node.effector.register_action(Telescoped)
def deref_telescoped(ctx: ActionContext, rid: Telescoped):
    msg: SlackMessage = rid.wrapped_rid
    p_msg = PersistentMessage(msg)
            
    if p_msg.status not in (MessageStatus.ACCEPTED, MessageStatus.ACCEPTED_ANON):
        return
    
    message_data = ctx.effector.deref(msg).contents
    channel_data = ctx.effector.deref(msg.channel).contents
    team_data = ctx.effector.deref(msg.workspace).contents
    author_data = ctx.effector.deref(p_msg.author).contents
    tagger_data = ctx.effector.deref(p_msg.tagger).contents
    
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
from rid_lib import RID
from rid_lib.types import SlackMessage, SlackUser, SlackChannel, SlackWorkspace
from slack_sdk.errors import SlackApiError
from .core import slack_app, effector
from .rid_types import Telescoped
from .persistent import PersistentMessage
from .constants import MessageStatus
from . import utils


# DEREFERENCE

@effector.register_dereference(SlackUser)
def deref_slack_user(rid: SlackUser):
    return slack_app.client.users_info(
        user=rid.user_id
    )["user"]

@effector.register_dereference(SlackMessage)
def deref_slack_message(rid: SlackMessage):
    def join_and_retry_on_err(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SlackApiError as err:
            if err.response["error"] == "not_in_channel":
                print("joining channel", rid.channel_id)
                slack_app.client.conversations_join(
                    channel=rid.channel_id
                )
                return func(*args, **kwargs)
            else:
                raise err

    return join_and_retry_on_err(
        func=slack_app.client.conversations_replies,
        channel=rid.channel_id,
        ts=rid.ts,
        limit=1
    )["messages"][0]

@effector.register_dereference(SlackChannel)
def deref_slack_channel(rid: SlackChannel):
    return slack_app.client.conversations_info(
        channel=rid.channel_id
    )["channel"]

@effector.register_dereference(SlackWorkspace)
def deref_slack_workspace(rid: SlackWorkspace):
    return slack_app.client.team_info(
        team=rid.team_id
    )["team"]
    
@effector.register_dereference(Telescoped)
def deref_telescoped(rid: Telescoped):
    msg: SlackMessage = rid.wrapped_rid
    p_msg = PersistentMessage(msg)
            
    if p_msg.status not in (MessageStatus.ACCEPTED, MessageStatus.ACCEPTED_ANON):
        return None
    
    message_data = effector.dereference(msg).contents
    channel_data = effector.dereference(msg.channel).contents
    team_data = effector.dereference(msg.workspace).contents
    author_data = effector.dereference(p_msg.author).contents
    tagger_data = effector.dereference(p_msg.tagger).contents
    
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
    
    return msg_json


 # TRANSFORM   

@effector.register("transform", SlackMessage)
def transform_slack_message_to_url(rid: SlackMessage):
    url_str = slack_app.client.chat_getPermalink(
        channel=rid.channel_id,
        message_ts=rid.ts
    )["permalink"]
    return RID.from_string(url_str)
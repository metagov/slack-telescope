from rid_lib import RID
from rid_lib.types import SlackMessage, SlackUser, SlackChannel, SlackWorkspace
from slack_sdk.errors import SlackApiError
from .core import slack_app, effector
from .rid_types import Telescoped
from .export import export_msg_to_json


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
    return export_msg_to_json(rid.wrapped_rid)


 # TRANSFORM   

@effector.register("transform", SlackMessage)
def transform_slack_message_to_url(rid: SlackMessage):
    url_str = slack_app.client.chat_getPermalink(
        channel=rid.channel_id,
        message_ts=rid.ts
    )["permalink"]
    return RID.from_string(url_str)
from rid_lib.core import RID
from rid_lib.types import SlackMessage, SlackUser

from .core import slack_app


def dereference_slack_user(user: SlackUser):
    resp = slack_app.client.users_profile_get(user=user.user_id)
    return resp["profile"]

def dereference_slack_message(msg: SlackMessage):
    resp = slack_app.client.conversations_replies(
        channel=msg.channel_id,
        ts=msg.message_id,
        limit=1
    )
    return resp["messages"][0]

dereference_table = {
    SlackUser: dereference_slack_user,
    SlackMessage: dereference_slack_message
}

def auto_dereference(rid: RID):
    dereference_func = dereference_table.get(type(rid))
    
    if dereference_func:
        return dereference_func(rid)
    else:
        raise Exception(f"No dereference func defined for '{type(rid)}'")
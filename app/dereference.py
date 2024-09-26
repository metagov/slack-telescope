from rid_lib.core import RID
from rid_lib.types import SlackMessage, SlackUser

from .core import slack_app, cache

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

def deref(rid: RID):
    dereference_func = dereference_table.get(type(rid))
    cache_obj = cache.read(rid)
        
    if cache_obj:
        print(rid, "hit cache")
        return cache_obj.data
    
    if dereference_func:
        print(rid, "dereferenced")
        data = dereference_func(rid)
        cache.write(rid, data)
        return data
    else:
        raise Exception(f"No dereference func defined for '{type(rid)}'")
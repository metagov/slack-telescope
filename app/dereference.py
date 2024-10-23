from rid_lib.core import RID
from rid_lib.types import SlackMessage, SlackUser, SlackChannel, HTTPS

from .core import slack_app, cache, trans_cache


dereference_table = {
    SlackUser:  
        lambda rid: slack_app.client.users_profile_get(
            user=rid.user_id
        )["profile"],

    SlackMessage:  
        lambda rid: slack_app.client.conversations_replies(
            channel=rid.channel_id, 
            ts=rid.message_id,
            limit=1
        )["messages"][0],
        
    SlackChannel: 
        lambda rid: slack_app.client.conversations_info(
            channel=rid.channel_id
        )["channel"]
}

def deref(rid: RID):
    dereference_func = dereference_table.get(type(rid))
    cache_obj = cache.read(rid)
        
    if cache_obj:
        print(rid, "hit deref cache")
        return cache_obj.data
    
    if dereference_func:
        print(rid, "dereferenced")
        data = dereference_func(rid)
        cache.write(rid, data)
        return data
    else:
        raise Exception(f"No dereference func defined for '{type(rid)}'")
    

def transform_slack_message_to_http(rid: SlackMessage):
    resp = slack_app.client.chat_getPermalink(
        channel=rid.channel_id,
        message_ts=rid.message_id
    )
    return RID.from_string(resp["permalink"])

transformation_table = {
    (SlackMessage, HTTPS): transform_slack_message_to_http
}    

def transform(rid: RID, to_type):
    transformation_func = transformation_table.get((type(rid), to_type))
    transformed = trans_cache.read(rid, to_type.context)
    
    if transformed:
        print(rid, "->", to_type.context, "hit trans cache")
        return transformed
    elif transformation_func:
        to_rid = transformation_func(rid)
        print(f"transformed {rid} -> {to_rid}")
        trans_cache.write(rid, to_rid)
        return to_rid
    else:
        raise Exception(f"No transformation func defined for '{type(rid)}' -> '{to_type}'")
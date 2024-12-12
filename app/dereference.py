from slack_sdk.errors import SlackApiError
from rid_lib.core import RID
from rid_lib.types import SlackMessage, SlackUser, SlackChannel, SlackWorkspace, HTTPS

from .core import slack_app, cache, trans_cache


dereference_table = {
    SlackUser.context:  
        lambda rid: slack_app.client.users_info(
            user=rid.user_id
        )["user"],

    SlackMessage.context:  
        lambda rid: slack_app.client.conversations_replies(
            channel=rid.channel_id, 
            ts=rid.ts,
            limit=1
        )["messages"][0],
        
    SlackChannel.context: 
        lambda rid: slack_app.client.conversations_info(
            channel=rid.channel_id
        )["channel"],
        
    SlackWorkspace.context:
        lambda rid: slack_app.client.team_info(
            team=rid.team_id
        )["team"]
}

def deref(rid: RID, refresh=False):
    dereference_func = dereference_table.get(rid.context)
    cache_obj = cache.read(rid)
        
    if cache_obj and not refresh:
        return cache_obj.data
    
    if dereference_func:
        while True:
            try:
                data = dereference_func(rid)
                cache.write(rid, data)
                return data
            except SlackApiError as e:
                if e.response["error"] == "not_in_channel":
                    print("joining channel", rid.channel_id)
                    slack_app.client.conversations_join(channel=rid.channel_id)
                else:
                    break
    else:
        raise Exception(f"No dereference func defined for '{type(rid)}'")
    

def transform_slack_message_to_http(rid: SlackMessage):
    resp = slack_app.client.chat_getPermalink(
        channel=rid.channel_id,
        message_ts=rid.ts
    )
    return RID.from_string(resp["permalink"])

transformation_table = {
    (SlackMessage, HTTPS): transform_slack_message_to_http
}    

def transform(rid: RID, to_type):
    transformation_func = transformation_table.get((type(rid), to_type))
    transformed = trans_cache.read(rid, to_type.context)
    
    if transformed:
        return transformed
    elif transformation_func:
        to_rid = transformation_func(rid)
        trans_cache.write(rid, to_rid)
        return to_rid
    else:
        raise Exception(f"No transformation func defined for '{type(rid)}' -> '{to_type}'")
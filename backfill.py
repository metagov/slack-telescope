import time
from slack_sdk.errors import SlackApiError
from rid_lib.types import SlackWorkspace, SlackChannel, SlackUser, SlackMessage

from app.core import slack_app, cache
from app import orchestrator


def observe_workspace():
    workspace = slack_app.client.team_info().data["team"]

    workspace_id = workspace["id"]
    workspace_rid = SlackWorkspace(workspace_id)
    
    print(workspace_rid, workspace["name"])
    
    channel_rids = []
    channels = get_channels()
    print("found", len(channels), "channels\n")
    
    for channel in channels:
        channel_id = channel["id"]
        channel_rid = observe_channel(channel, workspace_id)
        if channel_rid is None: continue
        
        print(channel_rid, "#" + channel["name"])
        channel_rids.append(channel_rid)
        
        if channel_id != "C06DMGNV7E0":
            continue
        
        observed_messages = 0
        total_messages = 0
        message_rids = []
        messages = get_messages(channel_id)
        print("found", len(messages), "messages\n")

        for message in messages:
            message_thread_id = message.get("thread_ts")
            
            total_messages += 1
            message_rid = observe_message(message, workspace_id, channel_id)
            
            if message_rid:
                print(message_rid)
            
            if message_thread_id is not None:
                if message_rid is None:
                    print("anonymous thread")
                
                threaded_message_rids = []
                threaded_messages = get_threaded_messages(channel_id, message_thread_id)
                print("found", len(threaded_messages), "threaded messages\n")
                
                for threaded_message in threaded_messages:
                    if threaded_message["ts"] == threaded_message["thread_ts"]: continue
                    total_messages += 1
                    threaded_message_rid = observe_message(threaded_message, workspace_id, channel_id)
                    if threaded_message_rid is None: continue
                    
                    observed_messages += 1
                    print("\t" + str(threaded_message_rid))
                    threaded_message_rids.append(threaded_message_rid)
                    
                print()
                # add threaded_messages to parent if parent was observed
                    
                    # make_request(CREATE, OBJECT_LINK, rid=message_rid, tag="has_messages", members=threaded_message_rids)
                # make_request(CREATE, OBJECT_LINK, rid=channel_rid, tag="has_messages", members=threaded_message_rids)
            
            if message_rid is None: continue
            
            observed_messages += 1
            message_rids.append(message_rid)
        
        print(channel_rid, "#" + channel["name"], f"observed {observed_messages}/{total_messages} messages")
        # add messages to channel
        # make_request(CREATE, OBJECT_LINK, rid=channel_rid, tag="has_messages", members=message_rids)
    # add channels to workspace
    # make_request(CREATE, OBJECT_LINK, rid=workspace_rid, tag="has_channels", members=channel_rids)

def get_channels():
    channel_cursor = None
    channels = []
    while not channels or channel_cursor:
        result = slack_app.client.conversations_list(cursor=channel_cursor).data
        channels.extend(result["channels"])
        channel_cursor = result.get("response_metadata", {}).get("next_cursor")

    # autojoin channels
    for channel in channels:    
        if not channel["is_member"] and not channel["is_archived"]:
            slack_app.client.conversations_join(channel=channel['id'])
            print("joined", channel["name"])
    
    return channels

def observe_channel(channel, workspace_id):
    if channel["is_member"] is False:
        return

    channel_id = channel["id"]
    channel_rid = SlackChannel(workspace_id, channel_id)
    # make_request(CREATE, OBJECT, rid=channel_rid, data=channel, overwrite=True)
    
    return channel_rid
    
def get_messages(channel_id):
    message_cursor = None
    messages = []
    while not messages or message_cursor:
        try:
            result = slack_app.client.conversations_history(channel=channel_id, limit=500, cursor=message_cursor)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                retry_after = int(e.response.headers["Retry-After"])
                print(f"timed out, waiting {retry_after} seconds")
                time.sleep(retry_after)
                result = slack_app.client.conversations_history(channel=channel_id, limit=500, cursor=message_cursor)
                
        messages.extend(result["messages"])
        has_more = result["has_more"]
        
        if has_more:
            message_cursor = result["response_metadata"]["next_cursor"]
        else:
            message_cursor = None
        
    return messages

def observe_message(message, workspace_id, channel_id):
    # prev fields ["user", "type", "ts", "text", "thread_ts"]
    
    if message.get("subtype"):
        return
    
    found_telescope = False
    reactions = message.get("reactions", [])
    for reaction in reactions:
        if reaction["name"] == "telescope":
            found_telescope = True
            tagger_rid = SlackUser(workspace_id, reaction["users"][-1])
            break
        
    if not found_telescope:
        return
    
    message_id = message["ts"]
    user_id = message["user"]
    
    message_rid = SlackMessage(workspace_id, channel_id, message_id)        
    author_rid = SlackUser(workspace_id, user_id)
    
    if author_rid.user_id != "U01G7NSR78S":
        return
    
    cache.write(message_rid, message)
    orchestrator.create_request_interaction(message_rid, author_rid, tagger_rid)

    return message_rid
            
def get_threaded_messages(channel_id, thread_id):
    threaded_message_cursor = None
    threaded_messages = []
    while not threaded_messages or threaded_message_cursor:
        try:
            result = slack_app.client.conversations_replies(channel=channel_id, ts=thread_id, limit=500, cursor=threaded_message_cursor)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                retry_after = int(e.response.headers["Retry-After"])
                print(f"timed out, waiting {retry_after} seconds")
                time.sleep(retry_after)
                result = slack_app.client.conversations_replies(channel=channel_id, ts=thread_id, limit=500, cursor=threaded_message_cursor)
                
        threaded_messages.extend(result["messages"])
        
        if result["has_more"]:
            threaded_message_cursor = result["response_metadata"]["next_cursor"]
        else:
            threaded_message_cursor = None
    
    return threaded_messages
    
            
if __name__ == "__main__":
    observe_workspace()
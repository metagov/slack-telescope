import time, json
from slack_sdk.errors import SlackApiError
from rid_lib.types import SlackMessage
from app.core import slack_app, cache
from app.config import TELESCOPE_EMOJI


filename = "backfill.json"
allowed_channels = ['CMAQ0785R', 'CMQD2LKUN', 'CVCTS9A3H', 'C011L4P8AES', 'C0175M3GLSU', 'C0270BXSYUC', 'C02VBLPR98E', 'C03218BFP8T', 'C034GUA938W', 'C036D1Y3LP9', 'C0495H5B12A', 'C04FU2ZGTT9', 'C04P6EGUYA3', 'C051WCSHYES', 'C063KJC5BF0', 'C06DMGNV7E0', 'C06LAQNLVNK', 'C06QDUPDA59', 'C071P0C0477']

try:
    with open(filename, "r") as f:
        records = json.load(f)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    records = {}

def write_records():
    with open(filename, "w") as f:
        json.dump(records, f, indent=2)

def auto_retry(function, **params):
    try:
        return function(**params)
    except SlackApiError as e:
        if e.response["error"] == "ratelimited":
            retry_after = int(e.response.headers["Retry-After"])
            print(f"timed out, waiting {retry_after} seconds")
            time.sleep(retry_after)
            return function(**params)
        else:
            print("unknown error", e)


team = slack_app.client.team_info().data["team"]
team_id = team["id"]

# get list of channels
channel_cursor = None
channels = []
while not channels or channel_cursor:
    result = slack_app.client.conversations_list(cursor=channel_cursor).data
    channels.extend(result["channels"])
    channel_cursor = result.get("response_metadata", {}).get("next_cursor")

for channel in channels:
    channel_id = channel["id"]
    
    if channel_id not in allowed_channels:
        print("#" + channel["name"], "(skipping disallowed channels)")
        continue
    
    if channel["is_archived"]:
        print("#" + channel["name"], "(skipping archived channels)")
        continue
    
    # join non member channels
    if not channel["is_member"]:
        slack_app.client.conversations_join(channel=channel['id'])
        print("joined", channel["name"])
    
    
    # if channel_id != "C071P0C0477":
    #     continue
    
    if (channel_id in records) and (records[channel_id]["completed"] == True):
        print("#" + channel["name"], "(skipping completed channels)")
        continue
    else:
        records[channel_id] = {
        "channel_name": channel["name"],
        "observed_messages": 0,
        "channel_messages": 0,
        "channel_replies": 0,
        "threaded_messages": 0,
        "total_messages": 0,
        "completed": False,
        "messages": []
    }
        
    c_record = records[channel_id]
    
    print("#" + channel["name"])

    # get list of messages in channel
    message_cursor = None
    messages = []
    while not messages or message_cursor:
        result = auto_retry(slack_app.client.conversations_history,
            channel=channel_id,
            limit=500,
            cursor=message_cursor
        )
        
        messages.extend(result["messages"])
        if result["has_more"]:
            message_cursor = result["response_metadata"]["next_cursor"]
        else:
            message_cursor = None


    for message in messages:
        message_rid = SlackMessage(team_id, channel_id, message["ts"])
        c_record["total_messages"] += 1
        c_record["channel_messages"] += 1
        
        # check for telescope reaction   
        found_telescope = False
        for reaction in message.get("reactions", []):
            if reaction["name"] == TELESCOPE_EMOJI:
                found_telescope = True
                break
        
        thread_ts = message.get("thread_ts")
        
        # ignore threaded messages sent to channel
        if thread_ts and (thread_ts != message["ts"]):
            c_record["channel_replies"] += 1
            print("🤫", message_rid)
            continue
        
        if found_telescope:
            print("✅", message_rid)
            cache.bundle_and_write(message_rid, message)
            c_record["observed_messages"] += 1
            c_record["messages"].append(str(message_rid))
            write_records()
        else:
            print("❌", message_rid)

        if thread_ts:
            threaded_message_cursor = None
            threaded_messages = []
            while not threaded_messages or threaded_message_cursor:
                result = auto_retry(slack_app.client.conversations_replies,
                    channel=channel_id,
                    ts=thread_ts,
                    limit=500,
                    cursor=threaded_message_cursor
                )
                        
                threaded_messages.extend(result["messages"])
                
                if result["has_more"]:
                    threaded_message_cursor = result["response_metadata"]["next_cursor"]
                else:
                    threaded_message_cursor = None
            
            c_record["threaded_messages"] += 1
            # don't double count thread parent message
            for threaded_message in threaded_messages[1:]:
                threaded_message_rid = SlackMessage(team_id, channel_id, threaded_message["ts"])
                c_record["total_messages"] += 1
                c_record["threaded_messages"] += 1
                
                # check for telescope reaction   
                found_telescope = False
                for reaction in threaded_message.get("reactions", []):
                    if reaction["name"] == TELESCOPE_EMOJI:
                        found_telescope = True
                        break
                
                if found_telescope:
                    print("\t✅", threaded_message_rid)
                    cache.bundle_and_write(threaded_message_rid, threaded_message)
                    c_record["observed_messages"] += 1
                    c_record["messages"].append(str(threaded_message_rid))
                    write_records()
                else:
                    print("\t❌", threaded_message_rid)
                    
    c_record["completed"] = True
    write_records()
    
    print(c_record["observed_messages"], "/", c_record["total_messages"], "messages observed in", "#" + channel["name"])
    print()

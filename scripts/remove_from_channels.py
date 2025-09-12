import time, json
from slack_sdk.errors import SlackApiError
from rid_lib.types import SlackMessage
from rid_lib.ext import Bundle
from koi_net_slack_telescope_node.core import slack_app, node


try:
    with open(node.config.telescope.backfill_file, "r") as f:
        records = json.load(f)
except (FileNotFoundError, json.decoder.JSONDecodeError):
    records = {}

def write_records():
    with open(node.config.telescope.backfill_file, "w") as f:
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

def remove_from_channels():
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
        
        if channel_id not in node.config.telescope.allowed_channels:
            if not channel["is_member"]:
                # print("#" + channel["name"], "(skipping disallowed channels)")
                continue
            
            slack_app.client.conversations_leave(channel=channel['id'])
            print("#" + channel["name"], "(leaving disallowed channels)")
            continue
        
        if channel["is_archived"]:
            # print("#" + channel["name"], "(skipping archived channels)")
            continue
        
        if channel["is_member"]:
            print("member of #" + channel["name"])
        
        # join non member channels
        # if not channel["is_member"]:
        #     slack_app.client.conversations_join(channel=channel['id'])
        #     print("joined", channel["name"])
        
        
        
if __name__ == "__main__":
    remove_from_channels()
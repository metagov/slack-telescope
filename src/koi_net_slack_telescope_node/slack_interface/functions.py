from slack_sdk.errors import SlackApiError
from rid_lib.types import SlackChannel, SlackUser, SlackMessage
from koi_net_slack_telescope_node.core import slack_app

def create_slack_msg(channel: SlackChannel | SlackUser, blocks=None, text=None):
    if isinstance(channel, SlackChannel):
        channel_id = channel.channel_id
    elif isinstance(channel, SlackUser):
        channel_id = channel.user_id
    
    response = slack_app.client.chat_postMessage(
        channel=channel_id,
        text=text,
        blocks=blocks,
        unfurl_links=False
    )
    
    return SlackMessage(
        response["message"]["team"],
        response["channel"],
        response["message"]["ts"]
    )
    
def update_slack_msg(msg: SlackMessage, blocks=None, text=None):
    slack_app.client.chat_update(
        channel=msg.channel_id,
        ts=msg.ts,
        text=text,
        blocks=blocks
    )
    
def delete_slack_msg(msg: SlackMessage, alt_text=None):
    try:
        slack_app.client.chat_delete(
            channel=msg.channel_id,
            ts=msg.ts
        )
    except SlackApiError as err:
        if err.response["error"] == "cant_delete_message":
            update_slack_msg(msg, blocks=[], text=alt_text or "_This message has been deleted._")
        else:
            raise err
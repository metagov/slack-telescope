from rid_lib import RID
from rid_lib.types import SlackChannel, SlackUser, SlackMessage
from app.core import slack_app

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
    
def delete_slack_msg(msg: SlackMessage):
    slack_app.client.chat_delete(
        channel=msg.channel_id,
        ts=msg.ts
    )
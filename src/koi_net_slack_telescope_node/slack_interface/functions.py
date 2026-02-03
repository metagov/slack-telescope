from dataclasses import dataclass

from slack_bolt import App
from slack_sdk.errors import SlackApiError
from rid_lib.types import SlackChannel, SlackUser, SlackMessage


@dataclass
class SlackFunctions:
    slack_app: App
    
    def create_msg(
        self, 
        channel: SlackChannel | SlackUser, 
        blocks=None, 
        text=None
    ):
        if isinstance(channel, SlackChannel):
            channel_id = channel.channel_id
        elif isinstance(channel, SlackUser):
            channel_id = channel.user_id
        
        response = self.slack_app.client.chat_postMessage(
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
        
    def update_msg(self, msg: SlackMessage, blocks=None, text=None):
        self.slack_app.client.chat_update(
            channel=msg.channel_id,
            ts=msg.ts,
            text=text,
            blocks=blocks
        )
        
    def delete_msg(self, msg: SlackMessage, alt_text=None):
        try:
            self.slack_app.client.chat_delete(
                channel=msg.channel_id,
                ts=msg.ts
            )
        except SlackApiError as err:
            if err.response["error"] == "cant_delete_message":
                self.update_msg(msg, blocks=[], text=alt_text or "_This message has been deleted._")
            else:
                raise err
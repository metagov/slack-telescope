from rid_lib.types import SlackMessage
from app.core import slack_app
from app.config import BROADCAST_CHANNEL_ID
from app.persistent import PersistentMessage
from app.components import *


def create_broadcast(message):
    p_message = PersistentMessage(message)
        
    resp = slack_app.client.chat_postMessage(
        text="New message observed",
        channel=BROADCAST_CHANNEL_ID,
        unfurl_links=False,
        blocks=[
            build_broadcast_msg_ref(message),
            build_msg_context_row(message),
        ]
    )
    
    p_message.broadcast_interaction = SlackMessage(
        resp["message"]["team"],
        resp["channel"],
        resp["message"]["ts"]
    )
    
def delete_broadcast(message: SlackMessage):
    p_message = PersistentMessage(message)
    
    slack_app.client.chat_delete(
        channel=p_message.broadcast_interaction.channel_id,
        ts=p_message.broadcast_interaction.message_id
    )
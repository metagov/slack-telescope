from app.core import slack_app
from app.persistent import PersistentMessage
from app.components import *

def refresh_request_interaction(message):
    p_message = PersistentMessage(message)
    
    slack_app.client.chat_update(
        channel=p_message.interaction.channel_id,
        ts=p_message.interaction.message_id,
        blocks=[
            build_request_msg_ref(message, p_message.author),
            build_msg_context_row(message, p_message.tagger),
            build_request_msg_status(message),
        ]
    )
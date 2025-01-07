from app.core import slack_app
from app.persistent import PersistentMessage
from app.slack_interface.components import *


def refresh_request_interaction(message):
    p_message = PersistentMessage(message)
    
    slack_app.client.chat_update(
        channel=p_message.request_interaction.channel_id,
        ts=p_message.request_interaction.ts,
        blocks=[
            build_request_msg_ref(message),
            build_msg_context_row(message),
            build_request_msg_status(message),
        ]
    )
    
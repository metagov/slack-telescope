from rid_lib.types import SlackMessage
from app.core import slack_app, graph
from app.persistent import PersistentMessage
from app.constants import MessageStatus
from app.components import *
from .helpers import refresh_request_interaction


def create_retract_interaction(message):
    p_message = PersistentMessage(message)
    
    resp = slack_app.client.chat_postMessage(
        channel=p_message.author.user_id,
        unfurl_links=False,
        blocks=[
            build_retract_msg_ref(message),
            build_msg_context_row(message, p_message.tagger),
            build_retract_interaction_row(message)
        ]
    )
    
    p_message.retract_interaction = SlackMessage(
        resp["message"]["team"],
        resp["channel"],
        resp["message"]["ts"]
    )
                    
    graph.create(p_message.author)
    graph.create(p_message.tagger)
    graph.create(message)
    graph.create_link(p_message.author, message, "wrote")
    graph.create_link(p_message.tagger, message, "tagged")
    
def handle_retract_interaction(action_id, message):
    p_message = PersistentMessage(message)
    p_message.status = MessageStatus.RETRACTED
    
    graph.delete(message)
    
    slack_app.client.chat_delete(
        channel=p_message.retract_interaction.channel_id,
        ts=p_message.retract_interaction.message_id
    )
    
    refresh_request_interaction(message)
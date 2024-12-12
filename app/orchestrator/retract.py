from rid_lib.types import SlackMessage
from app.core import slack_app, graph
from app.persistent import PersistentMessage
from app.constants import MessageStatus
from app.slack_interface.components import *
from app.utils import retraction_time_elapsed
from app.config import ENABLE_GRAPH
from app import messages
from .refresh import refresh_request_interaction
from .broadcast import delete_broadcast


def create_retract_interaction(message):
    p_message = PersistentMessage(message)
    
    resp = slack_app.client.chat_postMessage(
        text="Your message has been observed",
        unfurl_links=False,
        channel=p_message.author.user_id,
        blocks=[
            build_retract_msg_ref(message),
            build_msg_context_row(message),
            build_retract_interaction_row(message)
        ]
    )
    
    p_message.retract_interaction = SlackMessage(
        resp["message"]["team"],
        resp["channel"],
        resp["message"]["ts"]
    )
                    
    if ENABLE_GRAPH:
        graph.create(p_message.author)
        graph.create(p_message.tagger)
        graph.create(message)
        graph.create_link(p_message.author, message, "wrote")
        graph.create_link(p_message.tagger, message, "tagged")
    
def handle_retract_interaction(action_id, message):
    p_message = PersistentMessage(message)
    
    if not retraction_time_elapsed(p_message):
        if action_id == ActionId.RETRACT:
            print(f"Message <{message}> retracted")
            p_message.status = MessageStatus.RETRACTED
        
            if ENABLE_GRAPH:
                graph.delete(message)
                
            slack_app.client.chat_update(
                channel=p_message.retract_interaction.channel_id,
                ts=p_message.retract_interaction.ts,
                blocks=[
                    build_retract_msg_ref(message),
                    build_msg_context_row(message),
                    build_basic_context(messages.retract_success)
                ]
            )
        
            delete_broadcast(message)    
        
        elif action_id == ActionId.ANONYMIZE:
            print(f"Message <{message}> anonymized")
            p_message.status = MessageStatus.ACCEPTED_ANON
            
            slack_app.client.chat_update(
                channel=p_message.retract_interaction.channel_id,
                ts=p_message.retract_interaction.ts,
                blocks=[
                    build_retract_msg_ref(message),
                    build_msg_context_row(message),
                    build_basic_context(messages.anonymize_success)
                ]
            )
        
        refresh_request_interaction(message)
                        
    else:
        print(f"Message <{message}> could not be retracted")
        slack_app.client.chat_update(
            channel=p_message.retract_interaction.channel_id,
            ts=p_message.retract_interaction.ts,
            blocks=[
                build_retract_msg_ref(message),
                build_msg_context_row(message),
                build_basic_context(messages.retract_failure)
            ]
        )
        

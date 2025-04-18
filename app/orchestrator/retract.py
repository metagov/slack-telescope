from app.core import graph
from app.config import GRAPH_ENABLED
from app.persistent import PersistentMessage
from app.constants import MessageStatus
from app.slack_interface.functions import create_slack_msg, update_slack_msg
from app.slack_interface.composed import (
    retract_interaction_blocks, 
    end_retract_interaction_blocks, 
    end_request_interaction_blocks
)
from app.utils import retraction_time_elapsed
from app.constants import ActionId
from app import message_content
from .broadcast import delete_broadcast
from .message_handlers import handle_forget_message, handle_update_message


def create_retract_interaction(message):
    p_message = PersistentMessage(message)
    
    p_message.retract_interaction = create_slack_msg(
        p_message.author,
        text="Your message has been observed",
        blocks=retract_interaction_blocks(message)
    )
                    
    if GRAPH_ENABLED:
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
        
            if GRAPH_ENABLED:
                graph.delete(message)
            
            update_slack_msg(
                p_message.retract_interaction, 
                end_retract_interaction_blocks(
                    message, message_content.retract_success
                )
            )
            
            delete_broadcast(message)
            handle_forget_message(message)
        
        elif action_id == ActionId.ANONYMIZE:
            print(f"Message <{message}> anonymized")
            p_message.status = MessageStatus.ACCEPTED_ANON

            update_slack_msg(
                p_message.retract_interaction, 
                end_retract_interaction_blocks(
                    message, message_content.anonymize_success
                )
            )
            
            handle_update_message(message)
        
        update_slack_msg(p_message.request_interaction, end_request_interaction_blocks(message))
                        
    else:
        print(f"Message <{message}> could not be retracted")
        update_slack_msg(
            p_message.retract_interaction, 
            end_retract_interaction_blocks(
                message, message_content.retract_failure
            )
        )

        

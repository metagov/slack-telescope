import logging
from koi_net.protocol.event import EventType
from koi_net_slack_telescope_node.persistent import PersistentMessage
from koi_net_slack_telescope_node.constants import MessageStatus
from koi_net_slack_telescope_node.rid_types import Telescoped
from koi_net_slack_telescope_node.slack_interface.functions import create_slack_msg, update_slack_msg
from koi_net_slack_telescope_node.slack_interface.composed import (
    retract_interaction_blocks, 
    end_retract_interaction_blocks, 
    end_request_interaction_blocks
)
from koi_net_slack_telescope_node.utils import retraction_time_elapsed
from koi_net_slack_telescope_node.constants import ActionId
from koi_net_slack_telescope_node import message_content
from .broadcast import delete_broadcast
# from .message_handlers import handle_forget_message, handle_update_message
from ..core import node

logger = logging.getLogger(__name__)


def create_retract_interaction(message):
    p_message = PersistentMessage(message)
    
    p_message.retract_interaction = create_slack_msg(
        p_message.author,
        text="Your message has been observed",
        blocks=retract_interaction_blocks(message)
    )

def handle_retract_interaction(action_id, message):
    p_message = PersistentMessage(message)
    
    if not retraction_time_elapsed(p_message):
        if action_id == ActionId.RETRACT:
            logger.info(f"Message <{message}> retracted")
            p_message.status = MessageStatus.RETRACTED
        
            update_slack_msg(
                p_message.retract_interaction, 
                end_retract_interaction_blocks(
                    message, message_content.retract_success
                )
            )
            
            delete_broadcast(message)
            
            node.processor.handle(rid=Telescoped(message), event_type=EventType.FORGET)
            
            # handle_forget_message(message)
        
        elif action_id == ActionId.ANONYMIZE:
            logger.info(f"Message <{message}> anonymized")
            p_message.status = MessageStatus.ACCEPTED_ANON

            update_slack_msg(
                p_message.retract_interaction, 
                end_retract_interaction_blocks(
                    message, message_content.anonymize_success
                )
            )
            
            node.effector.deref(Telescoped(message), refresh_cache=True)
            
            # handle_update_message(message)
        
        update_slack_msg(p_message.request_interaction, end_request_interaction_blocks(message))
                        
    else:
        logger.info(f"Message <{message}> could not be retracted")
        update_slack_msg(
            p_message.retract_interaction, 
            end_retract_interaction_blocks(
                message, message_content.retract_failure
            )
        )

        

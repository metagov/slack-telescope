from slack_telescope_node.persistent import PersistentMessage, PersistentUser
from slack_telescope_node.constants import MessageStatus, UserStatus, ActionId
from slack_telescope_node.slack_interface.functions import (
    create_slack_msg,
    update_slack_msg, 
    delete_slack_msg
)
from slack_telescope_node.slack_interface.composed import (
    consent_welcome_msg_blocks,
    consent_interaction_blocks,
    end_request_interaction_blocks
)
from .retract import create_retract_interaction
from .broadcast import create_broadcast
from ..core import node, effector


def create_consent_interaction(message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)
    p_user.status = UserStatus.PENDING
        
    print(f"Sent consent interaction to user <{p_message.author}>")
    
    create_slack_msg(
        p_message.author,
        consent_welcome_msg_blocks()
    )
    
    p_message.consent_interaction = create_slack_msg(
        p_message.author,
        text="Requesting to observe your message",
        blocks=consent_interaction_blocks(message)
    )
    
def handle_consent_interaction(action_id, message):
    p_message = PersistentMessage(message)
    
    persistent_user = PersistentUser(p_message.author)
    persistent_user.status = action_id
    
    delete_slack_msg(p_message.consent_interaction)
    
    print(f"User <{p_message.author}> has set consent status to {action_id}")
    print(f"Handling message queue of size {len(persistent_user.msg_queue)}")
    
    while persistent_user.msg_queue:
        prev_message = persistent_user.dequeue()
        p_prev_message = PersistentMessage(prev_message)
        
        if action_id == ActionId.OPT_OUT:
            print(f"Message <{prev_message}> rejected")
            p_prev_message.status = MessageStatus.REJECTED
        
        elif action_id == ActionId.OPT_IN:
            print(f"Message <{prev_message}> accepted")
            p_prev_message.status = MessageStatus.ACCEPTED
            create_retract_interaction(message)
            create_broadcast(message)
            
            # bundle = effector.deref(prev_message, refresh=True)
            node.processor.handle(rid=prev_message)
            
            # handle_new_message(prev_message)
        
        elif action_id == ActionId.OPT_IN_ANON:
            print(f"Message <{prev_message}> accepted (anonymous)")
            p_prev_message.status = MessageStatus.ACCEPTED_ANON
            create_retract_interaction(message)
            create_broadcast(message)
            
            # bundle = effector.deref(prev_message, refresh=True)
            node.processor.handle(rid=prev_message)
            
            # handle_new_message(prev_message)
            
        update_slack_msg(p_message.request_interaction, end_request_interaction_blocks(message))
    
from rid_lib.types import SlackMessage
from app.rid_types import Telescoped
from app.core import slack_app, effector
from app.persistent import PersistentMessage, PersistentUser
from app.constants import MessageStatus, UserStatus, ActionId
from app.slack_interface.components import *
from app import messages
from .refresh import refresh_request_interaction
from .retract import create_retract_interaction
from .broadcast import create_broadcast


def create_consent_interaction(message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)
    p_user.status = UserStatus.PENDING
        
    print(f"Sent consent interaction to user <{p_message.author}>")
    
    slack_app.client.chat_postMessage(
        channel=p_message.author.user_id,
        unfurl_links=False,
        blocks=[
            build_basic_section(messages.consent_ui_welcome),
        ]
    )
    
    resp = slack_app.client.chat_postMessage(
        text="Requesting to observe your message",
        channel=p_message.author.user_id,
        unfurl_links=False,
        blocks=[
            build_consent_msg_ref(message),
            build_msg_context_row(message),
            build_consent_interaction_row(message)
        ]
    )
    
    p_message.consent_interaction = SlackMessage(
        resp["message"]["team"],
        resp["channel"],
        resp["message"]["ts"]
    )
    
def handle_consent_interaction(action_id, message):
    p_message = PersistentMessage(message)
    
    persistent_user = PersistentUser(p_message.author)
    persistent_user.status = action_id
    
    slack_app.client.chat_delete(
        channel=p_message.consent_interaction.channel_id,
        ts=p_message.consent_interaction.ts
    )
    
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
            create_retract_interaction(prev_message)
            create_broadcast(prev_message)
            effector.dereference(Telescoped(prev_message), refresh=True)
        
        elif action_id == ActionId.OPT_IN_ANON:
            print(f"Message <{prev_message}> accepted (anonymous)")
            p_prev_message.status = MessageStatus.ACCEPTED_ANON
            create_retract_interaction(prev_message)
            create_broadcast(prev_message)
            effector.dereference(Telescoped(prev_message), refresh=True)
            
        refresh_request_interaction(prev_message)
    
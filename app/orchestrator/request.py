from rid_lib.types import SlackMessage

from app.core import slack_app
from app.config import OBSERVATORY_CHANNEL_ID
from app.persistent import PersistentMessage, PersistentUser
from app.constants import MessageStatus, UserStatus, ActionId
from app.components import *
from .consent import create_consent_interaction
from .refresh import refresh_request_interaction
from .retract import create_retract_interaction
from .broadcast import create_broadcast


def create_request_interaction(message, author, tagger):
    print(f"{tagger} tagged message from {author}")
    
    p_message = PersistentMessage(message)
    
    # message previously been tagged and handled   
    if p_message.status != MessageStatus.UNSET:
        return
    
    p_message.status = MessageStatus.TAGGED
    p_message.author = author
    p_message.tagger = tagger
        
    resp = slack_app.client.chat_postMessage(
        channel=OBSERVATORY_CHANNEL_ID,
        unfurl_links=False,
        blocks=[
            build_request_msg_ref(message, author),
            build_msg_context_row(message, tagger),
            build_request_msg_status(message),
            build_request_interaction_row(message)
        ]
    )
    
    p_message.request_interaction = SlackMessage(
        resp["message"]["team"],
        resp["channel"],
        resp["message"]["ts"]
    )
    
def handle_request_interaction(action_id, message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)  
        
    if action_id == ActionId.REQUEST:
        if p_user.status == UserStatus.UNSET:
            create_consent_interaction(message)
            
        if p_user.status == UserStatus.PENDING:
            p_user.enqueue(message)
            p_message.status = MessageStatus.REQUESTED
            
        elif p_user.status == UserStatus.OPT_IN:
            p_message.status = MessageStatus.ACCEPTED
            create_retract_interaction(message)
            create_broadcast(message)
        
        elif p_user.status == UserStatus.OPT_IN_ANON:
            p_message.status = MessageStatus.ACCEPTED_ANON
            create_retract_interaction(message)
            create_broadcast(message)
            
        elif p_user.status == UserStatus.OPT_OUT:
            p_message.status = MessageStatus.REJECTED
        
        refresh_request_interaction(message)
    
    elif action_id == ActionId.IGNORE:
        p_message.status = MessageStatus.IGNORED
        
        slack_app.client.chat_update(
            channel=p_message.request_interaction.channel_id,
            ts=p_message.request_interaction.message_id,
            blocks=[
                build_request_msg_ref(message, p_message.author),
                build_msg_context_row(message, p_message.tagger),
                build_request_msg_status(message),
                build_alt_request_interaction_row(message)
            ]
        )
        
    
def handle_alt_request_interaction(action_id, message):
    p_message = PersistentMessage(message)
    
    if action_id == ActionId.UNDO_IGNORE:
        p_message.status = MessageStatus.TAGGED
        
        slack_app.client.chat_update(
            channel=p_message.request_interaction.channel_id,
            ts=p_message.request_interaction.message_id,
            blocks=[
                build_request_msg_ref(message, p_message.author),
                build_msg_context_row(message, p_message.tagger),
                build_request_msg_status(message),
                build_request_interaction_row(message)
            ]
        )

from rid_lib.types import SlackMessage

from app.core import slack_app
from app.config import OBSERVATORY_CHANNEL_ID
from app.persistent import PersistentMessage, PersistentUser
from app.constants import MessageStatus, UserStatus, ActionId
from app.components import *
from .consent import create_consent_interaction
from .retract import create_retract_interaction
from .helpers import refresh_request_interaction


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
    
    if action_id == ActionId.IGNORE:
        # slack_app.client.chat_delete(
        #     channel=p_message.request_interaction.channel_id,
        #     ts=p_message.request_interaction.message_id
        # )
        p_message.status = MessageStatus.IGNORED
        refresh_request_interaction(message)
        return
        
    if p_user.status == UserStatus.UNSET:
        create_consent_interaction(message)
        
    if p_user.status == UserStatus.PENDING:
        p_user.enqueue(message)
        p_message.status = MessageStatus.REQUESTED
        
    elif p_user.status in (UserStatus.OPT_IN, UserStatus.OPT_IN_ANON): 
        if p_user.msg_queue:
            print("Message queue should be empty:", p_user.msg_queue)
            
        p_message.status = MessageStatus.ACCEPTED
        
        if p_user.status == UserStatus.OPT_IN_ANON:
            p_message.anonymous = True
        
        create_retract_interaction(message)
        
    elif p_user.status == UserStatus.OPT_OUT:
        p_message.status = MessageStatus.REJECTED
        
    refresh_request_interaction(message)
    


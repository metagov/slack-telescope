from rid_lib.types import SlackMessage
from app.core import slack_app
from app.persistent import PersistentMessage, PersistentUser
from app.constants import MessageStatus, UserStatus, ActionId
from app.components import *
from .helpers import refresh_request_interaction
from .retract import create_retract_interaction


def create_consent_interaction(message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)
    p_user.status = UserStatus.PENDING
        
    resp = slack_app.client.chat_postMessage(
        channel=p_user.rid.user_id,
        unfurl_links=False,
        blocks=[
            build_consent_msg_ref(message),
            build_msg_context_row(message, p_message.tagger),
            build_consent_interaction_row(message),
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Your decision to opt in or out will apply to this message and all future messages observed by Telescope. If you chose to opt in, you will be informed when new messages are observed and have the option to retract them."
                }
            }
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
        ts=p_message.consent_interaction.message_id
    )
    
    while persistent_user.msg_queue:
        prev_message = persistent_user.dequeue()
        p_prev_message = PersistentMessage(prev_message)
        
        if action_id == ActionId.OPT_OUT:
            p_prev_message.status = MessageStatus.REJECTED
        
        else: 
            p_prev_message.status = MessageStatus.ACCEPTED
            
            if action_id == ActionId.OPT_IN_ANON:
                p_prev_message.anonymous = True
            
            create_retract_interaction(prev_message)
        refresh_request_interaction(prev_message)
    
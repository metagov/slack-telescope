from .constants import ActionId, BlockId, status_display
from .blocks import *
import messages

def build_request_msg_ref(message_url, tagger_name):    
    return section_block(
        text_obj(f"*{tagger_name}* tagged a <{message_url}|message>", type="mrkdwn")
    )
    
def build_consent_msg_ref(message_url):
    return section_block(
        text_obj(messages.consent_ui_msg_header.replace("message", f"<{message_url}|message>"), type="mrkdwn")
    )

def build_retract_msg_ref(message_url):
    return section_block(
        text_obj(messages.retract_ui_msg_header.replace("message", f"<{message_url}|message>"), type="mrkdwn")
    )
    
def build_broadcast_msg_ref(message_url):
    return section_block(
        text_obj(f"New <{message_url}|message> observed by Telescope", type="mrkdwn")
    )

def build_request_msg_status(message_status):    
    return context_block(
        elements=[
            text_obj("Status: " + status_display[message_status], type="mrkdwn")
        ]
    )
    
def build_basic_section(text):
    return section_block(
        text_obj(text, type="mrkdwn")
    )
    
def build_basic_context(text):
    return context_block(
        elements=[
            text_obj(text, type="mrkdwn")
        ]
    )
    
def build_request_interaction_row(rid):    
    return action_block(
        block_id=BlockId.REQUEST,
        elements=[
            button_block(ActionId.REQUEST, text_obj("Request"), str(rid), style="primary"),
            button_block(ActionId.IGNORE, text_obj("Ignore"), str(rid))
        ]
    )
    
def build_alt_request_interaction_row(rid):    
    return action_block(
        block_id=BlockId.REQUEST,
        elements=[
            button_block(ActionId.UNDO_IGNORE, text_obj("Undo Ignore"), str(rid))
        ]
    )
    
def build_consent_interaction_row(rid):    
    return action_block(
        block_id=BlockId.CONSENT,
        elements=[
            button_block(ActionId.OPT_IN, text_obj("Opt in"), str(rid)),
            button_block(ActionId.OPT_IN_ANON, text_obj("Opt in (anonymously)"), str(rid)),
            button_block(ActionId.OPT_OUT, text_obj("Opt out"), str(rid))
        ]
    )
    
def build_retract_interaction_row(rid):    
    return action_block(
        block_id=BlockId.RETRACT,
        elements=[
            button_block(ActionId.RETRACT, text_obj("Retract"), str(rid), style="danger")
        ]
    )
    
from .components import *
from slack_telescope_node import message_content

# REQUEST INTERACTION

# initial request interaction
def request_interaction_blocks(message):
    return [
        build_request_msg_ref(message),
        build_msg_context_row(message),
        build_request_msg_status(message),
        build_request_interaction_row(message)
    ]

# "unignore" request interaction
def alt_request_interaction_blocks(message):
    return [
        build_request_msg_ref(message),
        build_msg_context_row(message),
        build_request_msg_status(message),
        build_alt_request_interaction_row(message)
    ]

# "end" of request interaction, passive update to message status
def end_request_interaction_blocks(message):
    return [
        build_request_msg_ref(message),
        build_msg_context_row(message),
        build_request_msg_status(message),
    ]

# CONSENT INTERACTION

# welcome message with consent disclaimer
def consent_welcome_msg_blocks():
    return [
        build_basic_section(message_content.consent_ui_welcome),
    ]

# preview of first message requested and consent interaction
def consent_interaction_blocks(message):
    return [
        build_consent_msg_ref(message),
        build_msg_context_row(message),
        build_consent_interaction_row(message)
    ]

# BROADCAST INTERACTION

def broadcast_interaction_blocks(message):
    return [
        build_broadcast_msg_ref(message),
        build_msg_context_row(message),
    ]

# RETRACT INTERACTION

def retract_interaction_blocks(message):
    return [
        build_retract_msg_ref(message),
        build_msg_context_row(message),
        build_retract_interaction_row(message)
    ]

# end of retract interaction, display outcome "success/failure"
def end_retract_interaction_blocks(message, content):
    return [
        build_retract_msg_ref(message),
        build_msg_context_row(message),
        build_basic_context(content)
    ]
from rid_lib.types import HTTP
from .dereference import deref, transform
from .utils import format_msg


def build_msg_context_row(message, tagger):
    tagger_name = deref(tagger)["real_name"]
    permalink = str(transform(message, HTTP))
    return {
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"<#{message.channel_id}> | Tagged by {tagger_name} | <{permalink}|Jump to message>"
        }]
    }

def build_request_msg_ref(message, author):
    formatted_text = format_msg(message)
    author_name = deref(author)["real_name"]
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Posted by *{author_name}*\n{formatted_text}"
        }
    }
    
def build_consent_msg_ref(message):
    formatted_text = format_msg(message)
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Your message has been tagged for observation!\n{formatted_text}"
        }
    }

def build_retract_msg_ref(message):
    formatted_text = format_msg(message)
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Your message has been observed by Telescope!\n{formatted_text}"
        }
    }

def build_request_interaction_row(payload):
    return {
        "type": "actions",
        "block_id": "request",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Request"
                },
                "style": "primary",
                "action_id": "approve",
                "value": payload
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Ignore"
                },
                "action_id": "reject",
                "value": payload
            }
        ]
    }

def build_consent_interaction_row(payload):
    return {
        "type": "actions",
        "block_id": "consent",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Opt in"
                },
                "style": "primary",
                "action_id": "opt_in",
                "value": payload
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Opt in (anonymously)"
                },
                "style": "primary",
                "action_id": "opt_in_anon",
                "value": payload
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Opt out"
                },
                "action_id": "opt_out",
                "value": payload
            }
        ]
    }

def build_retract_interaction_row(payload):
    return {
        "type": "actions",
        "block_id": "retract",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Retract"
                },
                "style": "danger",
                "action_id": "retract",
                "value": payload
            }
        ]
    }
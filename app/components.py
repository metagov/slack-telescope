import re
from rid_lib.types import HTTPS, SlackUser
from .dereference import deref, transform
from .persistent import PersistentMessage
from .config import TEXT_PREVIEW_CHAR_LIMIT
from .constants import ActionId, BlockId, status_emojis
from .core import workspace_id


# formatting helper functions
def truncate_text(string: str):
    if len(string) > TEXT_PREVIEW_CHAR_LIMIT:
        return string[:TEXT_PREVIEW_CHAR_LIMIT] + "..."
    else:
        return string

def indent_text(string: str):
    return "\n".join([
        "&gt;" + line if line.startswith(("> ", "&gt; ")) else "&gt; " + line
        for line in string.splitlines()  
    ])

def filter_text(string: str):
    # replaces all @mentions
    def replace_match(match):
        try:
            user_data = deref(SlackUser(workspace_id, match.group(1)))
            if not user_data or type(user_data) != dict:
                return match.group(0)
            else:
                return "@" + user_data.get("real_name")
        except Exception:
            return match.group(0)
    
    return re.sub(r"<@(\w+)>", replace_match, string)
   
def format_text(string: str):
    return indent_text(filter_text(truncate_text(string)))


# build slack blocks
def build_msg_context_row(message, tagger):
    tagger_name = deref(tagger)["real_name"]
    permalink = str(transform(message, HTTPS))
    return {
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"<#{message.channel_id}> | Tagged by {tagger_name} | <{permalink}|Jump to message>"
        }]
    }

def build_request_msg_ref(message, author):
    formatted_text = format_text(deref(message)["text"])
    author_name = deref(author)["real_name"]
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Posted by *{author_name}*\n{formatted_text}"
        }
    }
    
def build_consent_msg_ref(message):
    formatted_text = format_text(deref(message)["text"])
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Your message has been tagged for observation!\n{formatted_text}"
        }
    }

def build_retract_msg_ref(message):
    formatted_text = format_text(deref(message)["text"])
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"Your message has been observed by Telescope!\n{formatted_text}"
        }
    }

def build_request_msg_status(message):
    status_text = PersistentMessage(message).status
    status_emoji = status_emojis[status_text]
    
    return {
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"Status: {status_text.capitalize()} {status_emoji}"
        }]
    }

def build_request_interaction_row(rid):
    payload = str(rid)
    return {
        "type": "actions",
        "block_id": BlockId.REQUEST,
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Request"
                },
                "style": "primary",
                "action_id": ActionId.REQUEST,
                "value": payload
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Ignore"
                },
                "action_id": ActionId.IGNORE,
                "value": payload
            }
        ]
    }

def build_consent_interaction_row(rid):
    payload = str(rid)
    return {
        "type": "actions",
        "block_id": BlockId.CONSENT,
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Opt in"
                },
                "style": "primary",
                "action_id": ActionId.OPT_IN,
                "value": payload
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Opt in (anonymously)"
                },
                "style": "primary",
                "action_id": ActionId.OPT_IN_ANON,
                "value": payload
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Opt out"
                },
                "action_id": ActionId.OPT_OUT,
                "value": payload
            }
        ]
    }

def build_retract_interaction_row(rid):
    payload = str(rid)
    return {
        "type": "actions",
        "block_id": BlockId.RETRACT,
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Retract"
                },
                "style": "danger",
                "action_id": ActionId.RETRACT,
                "value": payload
            }
        ]
    }
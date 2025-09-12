import re
from rid_lib.types import SlackUser
from koi_net_slack_telescope_node.constants import ActionId, BlockId, request_status_display
from koi_net_slack_telescope_node.persistent import PersistentMessage
from koi_net_slack_telescope_node.core import team_id, node
from koi_net_slack_telescope_node import message_content
from .blocks import *


def replace_match(match):
    try:
        user_data = node.effector.deref(SlackUser(team_id, match.group(1))).contents
        if not user_data or type(user_data) != dict:
            return match.group(0)
        else:
            return "@" + user_data.get("real_name")
    except Exception:
        return match.group(0)

def format_text(message):
    text = node.effector.deref(message).contents["text"]
            
    if len(text) > node.config.telescope.text_preview_char_limit:
        text = text[:node.config.telescope.text_preview_char_limit] + "..."
    
    text = text.replace("<!everyone>", "@ everyone")
    text = text.replace("<!channel>", "@ channel")
    text = text.replace("<!here>", "@ here")
    text = re.sub(r"<!subteam\^(\w+)>", "@ subteam", text)
    
    filtered_str = re.sub(r"<@(\w+)>", replace_match, text)
    indented_str = "\n".join([
        "&gt;" + line if line.startswith(("> ", "&gt; ")) else "&gt; " + line
        for line in filtered_str.splitlines()  
    ])
        
    return indented_str

def build_msg_context_row(message):
    p_message = PersistentMessage(message)
    author_name = node.effector.deref(p_message.author).contents.get(
        "real_name", f"<{p_message.author.user_id}>")
    
    timestamp = message.ts.split(".")[0]
        
    return context_block([
        text_obj(
            f"Posted in <#{message.channel_id}> by *{author_name}* | <!date^{timestamp}^{{date_pretty}} at {{time}}|(time unknown)> | <{p_message.permalink}|View message>",
            type="mrkdwn"
        )
    ])

def build_request_msg_ref(message):
    p_message = PersistentMessage(message)
    tagger_name = node.effector.deref(p_message.tagger).contents.get(
        "real_name", f"<{p_message.tagger.user_id}>")
       
    return section_block(
        text_obj(f"Tagged by *{tagger_name}*\n{format_text(message)}", type="mrkdwn")
    )
    
def build_consent_msg_ref(message):
    return section_block(
        text_obj(message_content.consent_ui_msg_header + f"\n{format_text(message)}", type="mrkdwn")
    )

def build_retract_msg_ref(message):
    return section_block(
        text_obj(message_content.retract_ui_msg_header + f"\n{format_text(message)}", type="mrkdwn")
    )
    
def build_broadcast_msg_ref(message):    
    return section_block(
        text_obj(format_text(message), type="mrkdwn")
    )

def build_request_msg_status(message):
    message_status = PersistentMessage(message).status
        
    return context_block([
        text_obj(f"Status: {request_status_display[message_status]}", type="mrkdwn")
    ])
    
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
            button_block(ActionId.UNDO_IGNORE, text_obj("Undo ignore"), str(rid))
        ]
    )
    
def build_consent_interaction_row(rid):    
    return action_block(
        block_id=BlockId.CONSENT,
        elements=[
            button_block(ActionId.OPT_IN, text_obj(":white_check_mark: Opt in"), str(rid)),
            button_block(ActionId.OPT_IN_ANON, text_obj(":warning: Opt in (anonymously)"), str(rid)),
            button_block(ActionId.OPT_OUT, text_obj(":x: Opt out"), str(rid))
        ]
    )
    
def build_retract_interaction_row(rid):    
    return action_block(
        block_id=BlockId.RETRACT,
        elements=[
            button_block(ActionId.RETRACT, text_obj("Retract"), str(rid), style="danger"),
            button_block(ActionId.ANONYMIZE, text_obj("Anonymize"), str(rid))
        ]
    )
import re
from dataclasses import dataclass

from koi_net.effector import Effector
from rid_lib import RID
from rid_lib.types import SlackMessage, SlackUser

from ..config import SlackTelescopeNodeConfig
from ..consts import ActionId, BlockId, request_status_display
from ..persistent import PersistentMessage
from .. import message_content


def text_obj(text: str, type="plain_text"):
    return {
        "type": type,
        "text": text
    }

def section_block(text_obj: dict[str, str]):
    return {
        "type": "section",
        "text": text_obj
    }

def context_block(elements: list):
    return {
        "type": "context",
        "elements": elements
    }
    
def action_block(block_id, elements: list):
    return {
        "type": "actions",
        "block_id": block_id,
        "elements": elements
    }
    
def button_block(action_id: str, text_obj: dict[str, str], value: str, style=None):
    return {
        "type": "button",
        "action_id": action_id,
        "value": value,
        "text": text_obj,
        **({"style": style} if style else {}),
    }

@dataclass
class BlockBuilder:
    effector: Effector
    config: SlackTelescopeNodeConfig
    
    def replace_match(self, match: re.Match[str]):
        try:
            user_data = self.effector.deref(
                SlackUser(
                    team_id=self.config.telescope.team_id, 
                    user_id=match.group(1)
                )).contents
            if not user_data or type(user_data) != dict:
                return match.group(0)
            else:
                return "@" + user_data.get("real_name")
        except Exception:
            return match.group(0)

    def format_text(self, message: SlackMessage):
        text: str = self.effector.deref(message).contents["text"]

        if len(text) > self.config.telescope.text_preview_char_limit:
            text = text[:self.config.telescope.text_preview_char_limit] + "..."
        
        text = text.replace("<!everyone>", "@ everyone")
        text = text.replace("<!channel>", "@ channel")
        text = text.replace("<!here>", "@ here")
        text = re.sub(r"<!subteam\^(\w+)>", "@ subteam", text)
        
        filtered_str = re.sub(r"<@(\w+)>", self.replace_match, text)
        indented_str = "\n".join([
            "&gt;" + line if line.startswith(("> ", "&gt; ")) else "&gt; " + line
            for line in filtered_str.splitlines()  
        ])
            
        return indented_str

    def build_msg_context_row(self, message: SlackMessage):
        p_message = PersistentMessage(message)
        author_name = self.effector.deref(p_message.author).contents.get(
            "real_name", f"<{p_message.author.user_id}>")
        
        timestamp = message.ts.split(".")[0]
            
        return context_block([
            text_obj(
                f"Posted in <#{message.channel_id}> by *{author_name}* | <!date^{timestamp}^{{date_pretty}} at {{time}}|(time unknown)> | <{p_message.permalink}|View message>",
                type="mrkdwn"
            )
        ])

    def build_request_msg_ref(self, message: SlackMessage):
        p_message = PersistentMessage(message)
        tagger_name = self.effector.deref(p_message.tagger).contents.get(
            "real_name", f"<{p_message.tagger.user_id}>")
        
        return section_block(
            text_obj(f"Tagged by *{tagger_name}*\n{self.format_text(message)}", type="mrkdwn")
        )
        
    def build_consent_msg_ref(self, message: SlackMessage):
        return section_block(
            text_obj(message_content.consent_ui_msg_header + f"\n{self.format_text(message)}", type="mrkdwn")
        )

    def build_retract_msg_ref(self, message: SlackMessage):
        return section_block(
            text_obj(message_content.retract_ui_msg_header + f"\n{self.format_text(message)}", type="mrkdwn")
        )
        
    def build_broadcast_msg_ref(self, message: SlackMessage):
        return section_block(
            text_obj(self.format_text(message), type="mrkdwn")
        )

    def build_request_msg_status(self, message: SlackMessage):
        message_status = PersistentMessage(message).status
            
        return context_block([
            text_obj(f"Status: {request_status_display[message_status]}", type="mrkdwn")
        ])
    
    def build_basic_section(self, text: str):
        return section_block(
            text_obj(text, type="mrkdwn")
        )
    
    def build_basic_context(self, text):
        return context_block(
            elements=[
                text_obj(text, type="mrkdwn")
            ]
        )
        
    def build_request_interaction_row(self, rid: RID):
        return action_block(
            block_id=BlockId.REQUEST,
            elements=[
                button_block(ActionId.REQUEST, text_obj("Request"), str(rid), style="primary"),
                button_block(ActionId.IGNORE, text_obj("Ignore"), str(rid))
            ]
        )
        
    def build_alt_request_interaction_row(self, rid: RID):
        return action_block(
            block_id=BlockId.REQUEST,
            elements=[
                button_block(ActionId.UNDO_IGNORE, text_obj("Undo ignore"), str(rid))
            ]
        )
        
    def build_consent_interaction_row(self, rid: RID):
        return action_block(
            block_id=BlockId.CONSENT,
            elements=[
                button_block(ActionId.OPT_IN, text_obj(":white_check_mark: Opt in"), str(rid)),
                button_block(ActionId.OPT_IN_ANON, text_obj(":warning: Opt in (anonymously)"), str(rid)),
                button_block(ActionId.OPT_OUT, text_obj(":x: Opt out"), str(rid))
            ]
        )
        
    def build_retract_interaction_row(self, rid: RID): 
        return action_block(
            block_id=BlockId.RETRACT,
            elements=[
                button_block(ActionId.RETRACT, text_obj("Retract"), str(rid), style="danger"),
                button_block(ActionId.ANONYMIZE, text_obj("Anonymize"), str(rid))
            ]
        )
        
    # initial request interaction
    def request_interaction_blocks(self, message: SlackMessage):
        return [
            self.build_request_msg_ref(message),
            self.build_msg_context_row(message),
            self.build_request_msg_status(message),
            self.build_request_interaction_row(message)
        ]

    # "unignore" request interaction
    def alt_request_interaction_blocks(self, message: SlackMessage):
        return [
            self.build_request_msg_ref(message),
            self.build_msg_context_row(message),
            self.build_request_msg_status(message),
            self.build_alt_request_interaction_row(message)
        ]

    # "end" of request interaction, passive update to message status
    def end_request_interaction_blocks(self, message: SlackMessage):
        return [
            self.build_request_msg_ref(message),
            self.build_msg_context_row(message),
            self.build_request_msg_status(message),
        ]

    # CONSENT INTERACTION

    # welcome message with consent disclaimer
    def consent_welcome_msg_blocks(self):
        return [
            self.build_basic_section(message_content.consent_ui_welcome),
        ]

    # preview of first message requested and consent interaction
    def consent_interaction_blocks(self, message: SlackMessage):
        return [
            self.build_consent_msg_ref(message),
            self.build_msg_context_row(message),
            self.build_consent_interaction_row(message)
        ]

    # BROADCAST INTERACTION

    def broadcast_interaction_blocks(self, message: SlackMessage):
        return [
            self.build_broadcast_msg_ref(message),
            self.build_msg_context_row(message),
        ]

    # RETRACT INTERACTION

    def retract_interaction_blocks(self, message: SlackMessage):
        return [
            self.build_retract_msg_ref(message),
            self.build_msg_context_row(message),
            self.build_retract_interaction_row(message)
        ]

    # end of retract interaction, display outcome "success/failure"
    def end_retract_interaction_blocks(self, message: SlackMessage, content: str):
        return [
            self.build_retract_msg_ref(message),
            self.build_msg_context_row(message),
            self.build_basic_context(content)
        ]
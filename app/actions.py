import json
from slack_bolt.context.say import Say
from slack_sdk.web.client import WebClient
from rid_lib.types import SlackMessage

from .persistent import PersistentUser, UserStatus
from .core import slack_app
from .utils import load_rid_from_json
from .components import *


# helper functions
def unpack_payload(payload_str: str):
    payload_json = load_rid_from_json(
        json.loads(payload_str))
    
    return payload_json["author"], payload_json["tagger"], payload_json["message"]

def unpack_action(action):
    return action["action_id"], action["value"]


@slack_app.action({"block_id": "request"})
def handle_request_action(ack, action, body, client: WebClient, say: Say):
    ack()
    
    interaction_rid = SlackMessage(
        workspace_id=body["team"]["id"],
        channel_id=body["channel"]["id"],
        message_id=body["message"]["ts"]
    )
    
    action_id, action_payload = unpack_action(action)
    author, tagger, message = unpack_payload(action_payload)
    
    if action_id == "reject":
        client.chat_delete(
            channel=interaction_rid.channel_id,
            ts=interaction_rid.message_id
        )
        return
    
    persistent_user = PersistentUser.safe_init(author)
    
    print(action_payload)
    
    if persistent_user.status == UserStatus.UNSET:
        # starting consent flow
        say(
            channel=author.user_id,
            unfurl_links=False,
            blocks=[
                build_consent_msg_ref(message),
                build_msg_context_row(message, tagger),
                build_consent_interaction_row(action_payload),
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Your decision to opt in or out will apply to this message and all future messages observed by Telescope. If you chose to opt in, you will be informed when new messages are observed and have the option to retract them."
                    }
                }
            ]
        )
        persistent_user.status = UserStatus.PENDING
    
    if persistent_user.status == UserStatus.PENDING:
        persistent_user.enqueue(message)
        
    elif persistent_user.status in (UserStatus.OPT_IN, UserStatus.OPT_IN_ANON): 
        
        if persistent_user.msg_queue:
            print("Message queue should be empty:", persistent_user.msg_queue)
        
        say(
            channel=author.user_id,
            unfurl_links=False,
            blocks=[
                build_retract_msg_ref(message),
                build_msg_context_row(message, tagger),
                build_retract_interaction_row(action_payload)
            ]
        )
        
        # case UserStatus.OPT_IN:
        #     # send retraction message
        #     ...
        # case UserStatus.OPT_IN_ANON:
        #     # send retraction message
        #     ...
    
    elif persistent_user.status == UserStatus.OPT_OUT:
        # case UserStatus.OPT_OUT:
        #     # ignore message
        ...
    
    
    # formatted_text = format_text(message_data["text"])
    
    # remove buttons from interaction message
    prev_blocks = body["message"]["blocks"]
    del prev_blocks[-1] 
    
    client.chat_update(
        channel=interaction_rid.channel_id,
        ts=interaction_rid.message_id,
        blocks=prev_blocks
    )
    
    
@slack_app.action({"block_id": "consent"})
def handle_consent_action(ack, action):
    ack()
    
    action_id, action_payload = unpack_action(action)
    author, tagger, message = unpack_payload(action_payload)
    
    persistent_user = PersistentUser.safe_init(author)
    persistent_user.status = action_id
    
    if action_id in (UserStatus.OPT_IN, UserStatus.OPT_IN_ANON):
        while persistent_user.msg_queue:
            msg: SlackMessage = persistent_user.dequeue()
            print(msg)
        
    elif action_id == UserStatus.OPT_OUT:
        persistent_user.msg_queue = []
        
        
@slack_app.action({"block_id": "retract"})
def handle_retract_action(ack, action):
    ack()
    
    action_id, action_payload = unpack_action(action)
    author, tagger, message = unpack_payload(action_payload)
    
    
    
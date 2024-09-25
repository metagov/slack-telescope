import json
from slack_bolt.context.say import Say
from slack_sdk.web.client import WebClient
from rid_lib.core import RID
from rid_lib.types import SlackMessage

from .core import slack_app
from .dereference import auto_dereference
from .utils import indent_text, truncate_text


@slack_app.action({
    "block_id": "pending_message",
    "action_id": "cancel_button"
})
def handle_cancel_action(ack, body, client: WebClient):
    ack()
    
    interaction_rid = SlackMessage(
        workspace_id=body["team"]["id"],
        channel_id=body["channel"]["id"],
        message_id=body["message"]["ts"]
    )
    
    client.chat_delete(
        channel=interaction_rid.channel_id,
        ts=interaction_rid.message_id
    )
    

@slack_app.action({
    "block_id": "pending_message",
    "action_id": "request_button"
})
def handle_block_action(ack, action, body, client: WebClient, say: Say):
    ack()
    
    interaction_rid = SlackMessage(
        workspace_id=body["team"]["id"],
        channel_id=body["channel"]["id"],
        message_id=body["message"]["ts"]
    )
    
    action_payload = {
        k: RID.from_string(v)
        for k, v in json.loads(action["value"]).items()
    }
    
    print(action_payload)
    
    user = action_payload["user"]
    message = action_payload["message"]
    message_data = auto_dereference(message)
    
    indented_text = indent_text(truncate_text(message_data["text"]))
    
    prev_blocks = body["message"]["blocks"]
    
    with open("blocks.json", "w") as f:
        json.dump(prev_blocks, f, indent=2)
    
    del prev_blocks[-1] 
    
    
    client.chat_update(
        channel=interaction_rid.channel_id,
        ts=interaction_rid.message_id,
        blocks=prev_blocks
    )
    
    say(
        channel=user.user_id,
        unfurl_links=False,
        text=indented_text,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your message has been tagged for observation!\n" + indented_text
                }
            },
            {
                "type": "actions",
                "block_id": "pending_message",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Opt-in"
                        },
                        "action_id": "opt_in_button",
                        "value": "action_payload"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Opt-in (anonymously)"
                        },
                        "action_id": "opt_in_anon_button",
                        "value": "action_payload"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Opt-out"
                        },
                        "action_id": "opt_out_button",
                        "value": "action_payload"
                    }
                ]
            }
        ]
    )

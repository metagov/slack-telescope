import json
from slack_bolt.context.say import Say
from rid_lib.core import RID

from .core import slack_app
from .dereference import auto_derefence
from .utils import indent_text, truncate_text


@slack_app.action({
    "block_id": "pending_message",
    "action_id": "request_button"
})
def handle_block_action(ack, action, say: Say):
    ack()
    
    action_payload = {
        k: RID.from_string(v)
        for k, v in json.loads(action["value"]).items()
    }
    
    print(action_payload)
    
    user = action_payload["user"]
    message = action_payload["message"]
    message_data = auto_derefence(message)
    
    indented_text = indent_text(truncate_text(message_data["text"]))
    
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
                        "style": "primary",
                        "action_id": "request_button",
                        "value": "action_payload"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Opt-out"
                        },
                        "style": "danger",
                        "action_id": "cancel_button",
                        "value": "action_payload"
                    }
                ]
            }
        ]
    )

from slack_sdk.web import WebClient
from slack_bolt.context.say import Say
from .core import slack_app
from .config import TELESCOPE_EMOJI
import json

print("Yo")

@slack_app.event("reaction_added")
def handle_reaction_added(event, client: WebClient, say: Say):    
    if event["item"]["type"] != "message":
        print("ignoring unsupported item")
        return
    
    if event["reaction"] != TELESCOPE_EMOJI:
        print("ignoring non telescope emoji")
        return
    
    item = event["item"]
    item_channel = item["channel"]
    item_user = event["item_user"]
    resp = client.conversations_replies(
        channel=item_channel,
        ts=item["ts"],
        limit=1
    )
    message = resp["messages"][0]
    
    resp = client.users_profile_get(user=event["user"])
    profile = resp["profile"]
    username = profile["real_name"]
    print(profile)
    user_img = profile["image_512"]
    
    resp = client.chat_getPermalink(
        channel=item_channel,
        message_ts=item["ts"]
    )
    permalink = resp["permalink"]
    
    print(json.dumps(message, indent=2))
    print(event["user"], event["reaction"], message["text"])
    
    say(
        unfurl_links=False,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{message['text']}```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<#{item_channel}> | Tagged by {username} | <{permalink}|Jump to message>"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "actionblock789",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Request"
                        },
                        "style": "primary",
                        "value": "click_me_456"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Cancel"
                        },
                        "value": "test"
                    }
                ]
            }
        ]
    )
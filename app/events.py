from slack_sdk.web import WebClient
from slack_bolt.context.say import Say
from .core import slack_app
from .config import TELESCOPE_EMOJI, TEXT_PREVIEW_CHAR_LIMIT
import json


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
    resp = client.conversations_replies(
        channel=item_channel,
        ts=item["ts"],
        limit=1
    )
    message = resp["messages"][0]
        
    resp = client.users_profile_get(user=event["user"])
    tagger_profile = resp["profile"]
    tagger_name = tagger_profile["real_name"]
    
    resp = client.users_profile_get(user=event["item_user"])
    author_profile = resp["profile"]
    author_name = author_profile["real_name"]
    
    resp = client.chat_getPermalink(
        channel=item_channel,
        message_ts=item["ts"]
    )
    permalink = resp["permalink"]
    
    print(json.dumps(message, indent=2))
    print(event["user"], event["reaction"], message["text"])
    
    message_text = message["text"]
    if len(message_text) > TEXT_PREVIEW_CHAR_LIMIT:
        truncated_text = message_text[:TEXT_PREVIEW_CHAR_LIMIT] + "..."
    else:
        truncated_text = message_text
        
    indented_text = "\n".join(
        ["> " + line for line in truncated_text.splitlines()])
        
    say(
        unfurl_links=False,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Posted by *{author_name}*\n" + indented_text
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"<#{item_channel}> | Tagged by {tagger_name} | <{permalink}|Jump to message>"
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
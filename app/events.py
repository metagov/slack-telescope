import json
from slack_sdk.web import WebClient
from slack_bolt.context.say import Say
from rid_lib.types import SlackMessage, SlackUser

from .core import slack_app
from .config import TELESCOPE_EMOJI
from .dereference import auto_dereference
from .utils import indent_text, truncate_text


@slack_app.event("reaction_added")
def handle_reaction_added(body, event, client: WebClient, say: Say):
    team_id = body["team_id"]
        
    if event["item"]["type"] != "message":
        print("ignoring unsupported item")
        return
    
    if event["reaction"] != TELESCOPE_EMOJI:
        print("ignoring non telescope emoji")
        return
        
    tagged_msg = SlackMessage(
        team_id, 
        event["item"]["channel"], 
        event["item"]["ts"]
    )
    tagger = SlackUser(team_id, event["user"])
    author = SlackUser(team_id, event["item_user"])
    
    if author.user_id == "U07LXBE9JFL":
        print("ignoring self authored message")
        return
    
    print(f"{tagger} tagged message from {author}")
    

    message_data = auto_dereference(tagged_msg)
    
    tagger_name = auto_dereference(tagger)["real_name"]
    author_name = auto_dereference(author)["real_name"]
    
    resp = client.chat_getPermalink(
        channel=tagged_msg.channel_id,
        message_ts=tagged_msg.message_id
    )
    permalink = resp["permalink"]
        
    indented_text = indent_text(truncate_text(message_data["text"]))
    
    action_payload = json.dumps({
        "user": str(author),
        "message": str(tagged_msg)
    })
    
    say(
        unfurl_links=False,
        text=indented_text,
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
                        "text": f"<#{tagged_msg.channel_id}> | Tagged by {tagger_name} | <{permalink}|Jump to message>"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "pending_message",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Request"
                        },
                        "style": "primary",
                        "action_id": "request_button",
                        "value": action_payload
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Ignore"
                        },
                        "action_id": "cancel_button",
                        "value": action_payload
                    }
                ]
            }
        ]
    )
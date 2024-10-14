import json, re
from slack_sdk.web import WebClient
from slack_bolt.context.say import Say
from rid_lib.types import SlackMessage, SlackUser, HTTP

from .core import slack_app
from .config import TELESCOPE_EMOJI, OBSERVATORY_CHANNEL_ID
from .components import *


@slack_app.event("reaction_added")
def handle_reaction_added(body, event, say: Say):
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
                
    action_payload = json.dumps({
        "author": str(author),
        "tagger": str(tagger),
        "message": str(tagged_msg)
    })
    
    say(
        channel=OBSERVATORY_CHANNEL_ID,
        unfurl_links=False,
        text=format_msg(tagged_msg),
        blocks=[
            build_request_msg_ref(tagged_msg, author),
            build_msg_context_row(tagged_msg, tagger),
            build_request_interaction_row(action_payload)
        ]
    )
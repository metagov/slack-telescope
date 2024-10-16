from rid_lib.types import SlackMessage, SlackUser

from .core import slack_app
from .config import TELESCOPE_EMOJI, SLACK_BOT_USER_ID
from . import orchestrator


@slack_app.event("reaction_added")
def handle_reaction_added(body, event):        
    if event["item"]["type"] != "message":
        print("ignoring unsupported item")
        return
    
    if event["reaction"] != TELESCOPE_EMOJI:
        print("ignoring non telescope emoji")
        return
    
    if event["item_user"] == SLACK_BOT_USER_ID:
        print("ignoring self authored message")
        return
    
    team_id = body["team_id"]
    tagged_msg = SlackMessage(
        team_id, 
        event["item"]["channel"], 
        event["item"]["ts"]
    )
    tagger = SlackUser(team_id, event["user"])
    author = SlackUser(team_id, event["item_user"])
    
    orchestrator.create_request_interaction(tagged_msg, author, tagger)
    
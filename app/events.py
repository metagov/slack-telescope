from rid_lib.types import SlackMessage, SlackUser
from .core import slack_app
from .config import TELESCOPE_EMOJI, SLACK_BOT_USER_ID, OBSERVATORY_CHANNEL_ID
from . import orchestrator
from .dereference import deref


@slack_app.event("reaction_added")
def handle_reaction_added(body, event):        
    if event["item"]["type"] != "message":
        return
    
    if event["reaction"] != TELESCOPE_EMOJI:
        return
    
    if event["item_user"] == SLACK_BOT_USER_ID:
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
    

@slack_app.event({
    "type": "message",
    "channel": OBSERVATORY_CHANNEL_ID
})
def handle_message_reply(event):
    # only handle replies to bot message
    if event.get("parent_user_id") != SLACK_BOT_USER_ID:
        return
    
    request_msg = SlackMessage(
        event["team"],
        event["channel"],
        event["thread_ts"]
    )
    
    
    slack_app.client.reactions_add(
        channel=event["channel"],
        timestamp=event["ts"],
        name="thumbsup"
    )
    
    breakpoint()

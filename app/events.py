from rid_lib.types import SlackMessage, SlackUser, SlackChannel
from .core import slack_app
from .config import TELESCOPE_EMOJI, SLACK_BOT_USER_ID
from .dereference import deref
from . import orchestrator


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
    channel = SlackChannel(tagged_msg.workspace_id, tagged_msg.channel_id)
    
    print(f"New message <{tagged_msg}> tagged in #{deref(channel)['name']} "
        f"(author: {deref(author)['real_name']}, "
        f"tagger: {deref(tagger)['real_name']})"
    )
        
    orchestrator.create_request_interaction(tagged_msg, author, tagger)
    
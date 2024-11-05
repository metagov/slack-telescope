from rid_lib.types import SlackMessage, SlackUser
from .core import slack_app, bot_user_id
from .config import TELESCOPE_EMOJI, OBSERVATORY_CHANNEL_ID
from . import orchestrator
from .persistent import PersistentMessage, get_linked_message
from .constants import MessageStatus

@slack_app.event("reaction_added")
def handle_reaction_added(body, event):        
    if event["item"]["type"] != "message":
        return
    
    team_id = body["team_id"]
    tagged_msg = SlackMessage(
        team_id, 
        event["item"]["channel"], 
        event["item"]["ts"]
    )
    emoji_str = event["reaction"]
    
    if event["item_user"] == bot_user_id:
        print(f"Adding '{emoji_str}' emoji to <{tagged_msg}>")
        p_msg = PersistentMessage(get_linked_message(tagged_msg))
        if p_msg.status != MessageStatus.UNSET:
            p_msg.add_emoji(emoji_str)
            
            # acknowledge emoji
            slack_app.client.reactions_add(
                channel=tagged_msg.channel_id,
                timestamp=tagged_msg.message_id,
                name=emoji_str
            )
    
    elif emoji_str == TELESCOPE_EMOJI:
        tagger = SlackUser(team_id, event["user"])
        author = SlackUser(team_id, event["item_user"])
            
        orchestrator.create_request_interaction(tagged_msg, author, tagger)
        
@slack_app.event("reaction_removed")
def handle_reaction_removed(body, event):
    if event["item"]["type"] != "message":
        return

    tagged_msg = SlackMessage(
        body["team_id"], 
        event["item"]["channel"], 
        event["item"]["ts"]
    )
    emoji_str = event["reaction"]

    if event["item_user"] == bot_user_id:
        print(f"Adding '{emoji_str}' emoji to <{tagged_msg}>")
        p_msg = PersistentMessage(get_linked_message(tagged_msg))
        if p_msg.status != MessageStatus.UNSET:
            num_reactions = p_msg.remove_emoji(emoji_str)
            
            # remove acknowledgement if all emojis are removed
            if num_reactions == 0:
                slack_app.client.reactions_remove(
                    channel=tagged_msg.channel_id,
                    timestamp=tagged_msg.message_id,
                    name=emoji_str
                )
            

@slack_app.event({
    "type": "message",
    "channel": OBSERVATORY_CHANNEL_ID
})
def handle_message_reply(event):
    # only handle replies to bot message
    if event.get("parent_user_id") != bot_user_id:
        return
    
    request_interaction = SlackMessage(
        event["team"],
        event["channel"],
        event["thread_ts"]
    )
        
    p_message = PersistentMessage(get_linked_message(request_interaction))
    p_message.add_comment(event["text"])
    
    slack_app.client.reactions_add(
        channel=event["channel"],
        timestamp=event["ts"],
        name="thumbsup"
    )
    
from rid_lib.types import SlackMessage, SlackUser
from slack_telescope_node.core import slack_app, bot_user
from slack_telescope_node.config import TELESCOPE_EMOJI, OBSERVATORY_CHANNEL_ID
from slack_telescope_node import orchestrator
from slack_telescope_node.persistent import PersistentMessage, get_linked_message
from slack_telescope_node.constants import MessageStatus
# from slack_telescope_node.orchestrator.message_handlers import handle_update_message
from ..core import node

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
    
    if event["item_user"] == bot_user.user_id:
        # only handle reqactions to interactions in the observatory
        if tagged_msg.channel_id != OBSERVATORY_CHANNEL_ID:
            return
        
        original_message = get_linked_message(tagged_msg)
        if original_message is None: return
        
        print(f"Adding '{emoji_str}' emoji to <{tagged_msg}>")
        p_msg = PersistentMessage(original_message)
        if p_msg.status != MessageStatus.UNSET:
            p_msg.add_emoji(emoji_str)
            
            # acknowledge emoji
            slack_app.client.reactions_add(
                channel=tagged_msg.channel_id,
                timestamp=tagged_msg.ts,
                name=emoji_str
            )
            
            # handle_update_message(p_msg.rid)
            node.processor.handle(rid=p_msg.rid)
    
    elif emoji_str == TELESCOPE_EMOJI:
        print("got a reaction")
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

    if event["item_user"] == bot_user.user_id:
        # only handle reqactions to interactions in the observatory
        if tagged_msg.channel_id != OBSERVATORY_CHANNEL_ID: return
        
        original_message = get_linked_message(tagged_msg)
        if original_message is None: return
        
        print(f"Removing '{emoji_str}' emoji from <{tagged_msg}>")
        p_msg = PersistentMessage(original_message)
        if p_msg.status != MessageStatus.UNSET:
            num_reactions = p_msg.remove_emoji(emoji_str)
            
            # remove acknowledgement if all emojis are removed
            if num_reactions == 0:
                slack_app.client.reactions_remove(
                    channel=tagged_msg.channel_id,
                    timestamp=tagged_msg.ts,
                    name=emoji_str
                )
            
            # handle_update_message(p_msg.rid)
            node.processor.handle(rid=p_msg.rid)
            

@slack_app.event({
    "type": "message",
    "channel": OBSERVATORY_CHANNEL_ID
})
def handle_message_reply(event):
    # only handle replies to bot message
    if event.get("parent_user_id") != bot_user.user_id:
        return
    
    replied_message = SlackMessage(
        event["team"],
        event["channel"],
        event["thread_ts"]
    )
        
    original_message = get_linked_message(replied_message)
    if original_message is None: return
    
    p_message = PersistentMessage(original_message)
    p_message.add_comment(event["text"])
    
    slack_app.client.reactions_add(
        channel=event["channel"],
        timestamp=event["ts"],
        name="thumbsup"
    )
    
    # handle_update_message(p_message.rid)
    node.processor.handle(rid=p_message.rid)
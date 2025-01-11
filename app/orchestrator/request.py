from app.core import effector, observatory_channel
from app.persistent import PersistentMessage, PersistentUser, create_link
from app.constants import MessageStatus, UserStatus, ActionId
from app.slack_interface.functions import create_slack_msg, update_slack_msg
from app.slack_interface.composed import (
    request_interaction_blocks, 
    alt_request_interaction_blocks,
    end_request_interaction_blocks
)
from .consent import create_consent_interaction
from .retract import create_retract_interaction
from .broadcast import create_broadcast
from .message_handlers import handle_message_accept


def create_request_interaction(message, author, tagger):    
    p_message = PersistentMessage(message)
    
    # message previously been tagged and handled   
    if p_message.status != MessageStatus.UNSET:
        return
    
    p_message.status = MessageStatus.TAGGED
    p_message.author = author
    p_message.tagger = tagger
    p_message.permalink = effector.transform(message)
    
    author_name = effector.deref(author).contents["real_name"]
    tagger_name = effector.deref(tagger).contents["real_name"]
    
    channel_data = effector.deref(message.channel).contents
    print(f"New message <{message}> tagged in #{channel_data['name']} "
        f"(author: {author_name}, tagger: {tagger_name})"
    )
    
    if channel_data["is_private"] == True:
        p_message.status = MessageStatus.UNREACHABLE
        
        create_slack_msg(observatory_channel, text=f"The <{p_message.permalink}|message you just tagged> is located in a private channel and cannot be observed.")
        print("Message was unreachable")
        return
    
    p_message.request_interaction = create_slack_msg(
        observatory_channel,
        request_interaction_blocks(message)
    )
    
    create_link(p_message.request_interaction, message)
    
def handle_request_interaction(action_id, message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)
    author = effector.deref(p_message.author).contents
    
    print(f"Handling request interaction action: '{action_id}' for message <{message}>")
    if action_id == ActionId.REQUEST:
        print(f"User <{p_message.author}> status is: '{p_user.status}'")
        if p_user.status == UserStatus.UNSET:
            
            # bots can't consent, opt in by default
            if author["is_bot"]:
                p_user.status = UserStatus.OPT_IN
            else:
                create_consent_interaction(message)
            
        if p_user.status == UserStatus.PENDING:
            print(f"Queued message <{message}>")
            p_user.enqueue(message)
            p_message.status = MessageStatus.REQUESTED
            
        elif p_user.status == UserStatus.OPT_IN:
            print(f"Message <{message}> accepted")
            p_message.status = MessageStatus.ACCEPTED
            create_retract_interaction(message)
            create_broadcast(message)
            handle_message_accept(message)
            
        elif p_user.status == UserStatus.OPT_IN_ANON:
            print(f"Message <{message}> accepted (anonymous)")
            p_message.status = MessageStatus.ACCEPTED_ANON
            create_retract_interaction(message)
            create_broadcast(message)
            handle_message_accept(message)
             
        elif p_user.status == UserStatus.OPT_OUT:
            print(f"Message <{message}> rejected")
            p_message.status = MessageStatus.REJECTED
        
        update_slack_msg(
            p_message.request_interaction, 
            end_request_interaction_blocks(message)
        )
    
    elif action_id == ActionId.IGNORE:
        print(f"Message <{message}> ignored")
        p_message.status = MessageStatus.IGNORED
        
        update_slack_msg(
            p_message.request_interaction,
            alt_request_interaction_blocks(message)
        )
            
    elif action_id == ActionId.UNDO_IGNORE:
        print(f"Message <{message}> unignored")
        p_message.status = MessageStatus.TAGGED
        
        update_slack_msg(
            p_message.request_interaction,
            request_interaction_blocks(message)
        )

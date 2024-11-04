from rid_lib.types import SlackMessage, SlackChannel, HTTPS

from app.core import slack_app
from app.config import OBSERVATORY_CHANNEL_ID
from app.persistent import PersistentMessage, PersistentUser, create_link
from app.constants import MessageStatus, UserStatus, ActionId
from app.components import *
from app.dereference import deref, transform
from .consent import create_consent_interaction
from .refresh import refresh_request_interaction
from .retract import create_retract_interaction
from .broadcast import create_broadcast


def create_request_interaction(message, author, tagger):    
    p_message = PersistentMessage(message)
    
    # message previously been tagged and handled   
    if p_message.status != MessageStatus.UNSET:
        return
    
    p_message.status = MessageStatus.TAGGED
    p_message.author = author
    p_message.tagger = tagger
    p_message.permalink = transform(message, HTTPS)
    
    author_name = deref(author)["real_name"]
    tagger_name = deref(tagger)["real_name"]
    
    
    channel = SlackChannel(message.workspace_id, message.channel_id)
    channel_data = deref(channel)
    print(f"New message <{message}> tagged in #{channel_data['name']} "
        f"(author: {author_name}, "
        f"tagger: {tagger_name})"
    )
    
    if channel_data["is_private"] == True:
        p_message.status = MessageStatus.UNREACHABLE
        slack_app.client.chat_postMessage(
            channel=OBSERVATORY_CHANNEL_ID,
            text=f"The <{p_message.permalink}|message you just tagged> is located in a private channel and cannot be observed.")
        print("Message was unreachable")
        return
    
    resp = slack_app.client.chat_postMessage(
        channel=OBSERVATORY_CHANNEL_ID,
        unfurl_links=False,
        blocks=[
            build_request_msg_ref(message),
            build_msg_context_row(message),
            build_request_msg_status(message),
            build_request_interaction_row(message)
        ]
    )
    
    p_message.request_interaction = SlackMessage(
        resp["message"]["team"],
        resp["channel"],
        resp["message"]["ts"]
    )
    
    create_link(p_message.request_interaction, message)
    
def handle_request_interaction(action_id, message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)
    author = deref(p_message.author)
            
    if action_id == ActionId.REQUEST:
        print(f"Message <{message}> requested")
        
        if p_user.status == UserStatus.UNSET:
            print(f"User <{p_message.author}> status is unset")
            
            if author["is_bot"]:
                p_user.status = UserStatus.OPT_IN
            else:
                create_consent_interaction(message)
            
        if p_user.status == UserStatus.PENDING:
            print(f"User <{p_message.author}> status is pending")
            print(f"Queued message <{message}>")
            p_user.enqueue(message)
            p_message.status = MessageStatus.REQUESTED
            
        elif p_user.status == UserStatus.OPT_IN:
            print(f"User <{p_message.author}> status is opt in")
            print(f"Message <{message}> accepted")
            p_message.status = MessageStatus.ACCEPTED
            create_retract_interaction(message)
            create_broadcast(message)
        
        elif p_user.status == UserStatus.OPT_IN_ANON:
            print(f"User <{p_message.author}> status is opt in (anonymous)")
            print(f"Message <{message}> accepted (anonymous)")
            p_message.status = MessageStatus.ACCEPTED_ANON
            create_retract_interaction(message)
            create_broadcast(message)
            
        elif p_user.status == UserStatus.OPT_OUT:
            print(f"User <{p_message.author}> status is opt out, rejecting message")
            print(f"Message <{message}> rejected")
            p_message.status = MessageStatus.REJECTED
        
        refresh_request_interaction(message)
    
    elif action_id == ActionId.IGNORE:
        print(f"Message <{message}> ignored")
        p_message.status = MessageStatus.IGNORED
        
        slack_app.client.chat_update(
            channel=p_message.request_interaction.channel_id,
            ts=p_message.request_interaction.message_id,
            blocks=[
                build_request_msg_ref(message),
                build_msg_context_row(message),
                build_request_msg_status(message),
                build_alt_request_interaction_row(message)
            ]
        )
            
    elif action_id == ActionId.UNDO_IGNORE:
        print(f"Message <{message}> unignored")
        p_message.status = MessageStatus.TAGGED
        
        slack_app.client.chat_update(
            channel=p_message.request_interaction.channel_id,
            ts=p_message.request_interaction.message_id,
            blocks=[
                build_request_msg_ref(message),
                build_msg_context_row(message),
                build_request_msg_status(message),
                build_request_interaction_row(message)
            ]
        )

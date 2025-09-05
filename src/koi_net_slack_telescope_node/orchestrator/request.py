import logging
from functools import lru_cache
from rid_lib import RID
from rid_lib.types import SlackMessage, SlackUser
from ..core import node, slack_app, observatory_channel
from ..persistent import PersistentMessage, PersistentUser, create_link
from ..constants import MessageStatus, UserStatus, ActionId
from ..slack_interface.functions import create_slack_msg, update_slack_msg
from ..slack_interface.composed import (
    request_interaction_blocks, 
    alt_request_interaction_blocks,
    end_request_interaction_blocks
)
from .consent import create_consent_interaction
from .retract import create_retract_interaction
from .broadcast import create_broadcast
from ..rid_types import Telescoped
from ..core import node
# from .message_handlers import handle_new_message

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def slack_message_rid_to_url(rid: SlackMessage):
    url_str = slack_app.client.chat_getPermalink(
        channel=rid.channel_id,
        message_ts=rid.ts
    )["permalink"]
    return RID.from_string(url_str)

def create_request_interaction(
    message: SlackMessage, 
    author: SlackUser, 
    tagger: SlackUser
):    
    p_message = PersistentMessage(message)
    
    # message previously been tagged and handled   
    if p_message.status != MessageStatus.UNSET:
        return
    
    p_message.status = MessageStatus.TAGGED
    p_message.author = author
    p_message.tagger = tagger
    p_message.permalink = slack_message_rid_to_url(message)
    
    author_data = node.effector.deref(author).contents
    author_name = author_data.get("real_name", f"<{author.user_id}>")
    tagger_name = node.effector.deref(tagger).contents.get(
        "real_name", f"<{tagger.user_id}>")
    
    channel_data = node.effector.deref(message.channel).contents
    logger.debug(f"New message <{message}> tagged in #{channel_data['name']} "
        f"(author: {author_name}, tagger: {tagger_name})"
    )
    
    if channel_data["is_private"] == True:
        p_message.status = MessageStatus.UNREACHABLE
        
        create_slack_msg(observatory_channel, text=f"The <{p_message.permalink}|message you just tagged> is located in a private channel and cannot be observed.")
        logger.debug("Message was unreachable")
        return
    
    if author_data["deleted"] == True:
        p_message.status = MessageStatus.UNREACHABLE
        
        create_slack_msg(observatory_channel, text=f"The <{p_message.permalink}|message you just tagged> was authored by the deactivated account <@{author.user_id}> and cannot give consent.")
        logger.debug("Message was authored by deleted user")
        return
    
    p_message.request_interaction = create_slack_msg(
        observatory_channel,
        request_interaction_blocks(message)
    )
    
    create_link(p_message.request_interaction, message)
    
def handle_request_interaction(action_id, message):
    p_message = PersistentMessage(message)
    p_user = PersistentUser(p_message.author)
    author = node.effector.deref(p_message.author).contents
    
    logger.debug(f"Handling request interaction action: '{action_id}' for message <{message}>")
    if action_id == ActionId.REQUEST:
        logger.debug(f"User <{p_message.author}> status is: '{p_user.status}'")
        if p_user.status == UserStatus.UNSET:
            
            # bots can't consent, opt in by default
            if author["is_bot"]:
                p_user.status = UserStatus.OPT_IN
            else:
                create_consent_interaction(message)
            
        if p_user.status == UserStatus.PENDING:
            logger.info(f"Queued message <{message}>")
            p_user.enqueue(message)
            p_message.status = MessageStatus.REQUESTED
            
        elif p_user.status == UserStatus.OPT_IN:
            logger.info(f"Message <{message}> accepted")
            p_message.status = MessageStatus.ACCEPTED
            create_retract_interaction(message)
            create_broadcast(message)
            
            node.effector.deref(Telescoped(message))
            
            # handle_new_message(message)
            
        elif p_user.status == UserStatus.OPT_IN_ANON:
            logger.info(f"Message <{message}> accepted (anonymous)")
            p_message.status = MessageStatus.ACCEPTED_ANON
            create_retract_interaction(message)
            create_broadcast(message)
            
            node.effector.deref(Telescoped(message))

            # handle_new_message(message)
             
        elif p_user.status == UserStatus.OPT_OUT:
            logger.info(f"Message <{message}> rejected")
            p_message.status = MessageStatus.REJECTED
        
        update_slack_msg(
            p_message.request_interaction, 
            end_request_interaction_blocks(message)
        )
    
    elif action_id == ActionId.IGNORE:
        logger.info(f"Message <{message}> ignored")
        p_message.status = MessageStatus.IGNORED
        
        update_slack_msg(
            p_message.request_interaction,
            alt_request_interaction_blocks(message)
        )
            
    elif action_id == ActionId.UNDO_IGNORE:
        logger.info(f"Message <{message}> unignored")
        p_message.status = MessageStatus.TAGGED
        
        update_slack_msg(
            p_message.request_interaction,
            request_interaction_blocks(message)
        )

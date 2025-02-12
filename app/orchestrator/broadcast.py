from rid_lib.types import SlackMessage
from app.core import broadcast_channel
from app.persistent import PersistentMessage
from app.slack_interface.functions import create_slack_msg, delete_slack_msg
from app.slack_interface.composed import broadcast_interaction_blocks


def create_broadcast(message):
    p_message = PersistentMessage(message)
    
    p_message.broadcast_interaction = create_slack_msg(
        broadcast_channel,
        broadcast_interaction_blocks(message)
    )    
    
def delete_broadcast(message: SlackMessage):
    p_message = PersistentMessage(message)
    
    delete_slack_msg(p_message.broadcast_interaction)
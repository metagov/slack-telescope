from rid_lib.types import SlackMessage
from koi_net_slack_telescope_node.core import broadcast_channel
from koi_net_slack_telescope_node.persistent import PersistentMessage
from koi_net_slack_telescope_node.slack_interface.functions import create_slack_msg, delete_slack_msg
from koi_net_slack_telescope_node.slack_interface.composed import broadcast_interaction_blocks


def create_broadcast(message):
    p_message = PersistentMessage(message)
    
    p_message.broadcast_interaction = create_slack_msg(
        broadcast_channel,
        broadcast_interaction_blocks(message)
    )    
    
def delete_broadcast(message: SlackMessage):
    p_message = PersistentMessage(message)
    
    delete_slack_msg(p_message.broadcast_interaction, alt_text="_This message has been retracted._")
from koi_net.protocol.event import Event, EventType
from slack_telescope_node.rid_types import Telescoped
from slack_telescope_node.core import effector, node
from slack_telescope_node.slack_interface.components import *

# TODO: refactor

def handle_new_message(message):
    t_message = Telescoped(message)
    bundle = effector.deref(t_message, refresh=True)
    
    coordinator_interface.broadcast_event(
        Event(
            t_message,
            EventType.NEW,
            bundle.manifest
        )
    )

def handle_update_message(message):
    t_message = Telescoped(message)
    bundle = effector.deref(t_message, refresh=True)
        
    coordinator_interface.broadcast_event(
        Event(
            t_message,
            EventType.UPDATE,
            bundle.manifest
        )
    )

def handle_forget_message(message):    
    t_message = Telescoped(message)
    cache.delete(t_message)
        
    coordinator_interface.broadcast_event(
        Event(
            t_message,
            EventType.FORGET
        )
    )
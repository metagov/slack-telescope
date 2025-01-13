from rid_lib.ext import Event, EventType
from app.rid_types import Telescoped
from app.core import effector, cache
from app.slack_interface.components import *
from app import coordinator_interface


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
from rid_lib.ext import Event, EventType
from app.rid_types import Telescoped
from app.core import effector, cache
from app.slack_interface.components import *
from app import coordinator


def accept_and_coordinate(message):
    t_message = Telescoped(message)
    bundle = effector.dereference(t_message, refresh=True)
    
    coordinator.broadcast_event(
        Event(
            t_message,
            EventType.NEW,
            bundle.manifest
        )
    )

def anonymize_and_coordinate(message):
    t_message = Telescoped(message)
    bundle = effector.dereference(t_message, refresh=True)
    
    print(bundle)
    
    coordinator.broadcast_event(
        Event(
            t_message,
            EventType.UPDATE,
            bundle.manifest
        )
    )

def retract_and_coordinate(message):
    t_message = Telescoped(message)
    cache.delete(t_message)
        
    coordinator.broadcast_event(
        Event(
            t_message,
            EventType.FORGET
        )
    )

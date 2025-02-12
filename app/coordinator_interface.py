import secrets
from rid_lib.ext import Event, Cache, EventType, CacheBundle
from app import sensor_interface

coordinator_cache = Cache("coordinator_cache")

subscribers: dict[str, list[Event]] = {}

def broadcast_event(event: Event):
    print(f"Broadcasting event to coordinator:", event)
    
    for sub_id in subscribers.keys():
        subscribers[sub_id].append(event)
        
        if len(subscribers[sub_id]) > 100:
            del subscribers[sub_id]
            
    if event.event_type in (EventType.NEW, EventType.UPDATE):
        coordinator_cache.write(
            event.rid, CacheBundle(event.manifest))
    elif event.event_type == EventType.FORGET:
        coordinator_cache.delete(event.rid)
        
def refresh():
    rids = sensor_interface.get_rids()
    
    for rid in rids:
        bundle = sensor_interface.get_object(rid)
        if bundle:
            coordinator_cache.write(rid, bundle)
            
def register_subscriber():
    sub_id = secrets.token_urlsafe(16)
    subscribers[sub_id] = []
    return sub_id

def poll_events(sub_id: str):
    if sub_id not in subscribers:
        return
    events = subscribers[sub_id]
    subscribers[sub_id] = []
    return events
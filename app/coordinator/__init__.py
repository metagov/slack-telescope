import json
from rid_lib.ext import Event, Cache, EventType, CacheBundle

coordinator_cache = Cache("coordinator_cache")

def broadcast_event(event: Event):
    print(f"broadcasting {event.event_type} event:\n{json.dumps(event.to_json(), indent=2)}")
    
    if event.event_type in (EventType.NEW, EventType.UPDATE):
        coordinator_cache.write(
            event.rid, CacheBundle(event.manifest)
        )
    elif event.event_type == EventType.FORGET:
        coordinator_cache.delete(event.rid)
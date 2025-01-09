import json
from rid_lib.ext import Event, Cache, EventType, CacheBundle
from app.persistent import retrieve_all_rids
from app.rid_types import Telescoped
from app.core import effector
from app import sensor_interface

coordinator_cache = Cache("coordinator_cache")

def broadcast_event(event: Event):
    print(f"broadcasting {event.event_type} event:\n{json.dumps(event.to_json(), indent=2)}")
    
    if event.event_type in (EventType.NEW, EventType.UPDATE):
        coordinator_cache.write(
            event.rid, CacheBundle(event.manifest)
        )
    elif event.event_type == EventType.FORGET:
        coordinator_cache.delete(event.rid)
        
def refresh():
    rids = sensor_interface.get_rids()
    
    for rid in rids:
        bundle = sensor_interface.get_object(rid)
        if bundle:
            coordinator_cache.write(rid, bundle)
    
# if not coordinator_cache.read_all_rids():
#     print("filling empty coordinator cache")
#     refresh()

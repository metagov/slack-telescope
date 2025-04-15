from fastapi import APIRouter, Query, Depends, HTTPException, status
from rid_lib.core import RID
from rid_lib.ext.utils import json_serialize
from app import sensor_interface, coordinator_interface
from .auth import verify_api_key

router = APIRouter(
    dependencies=[Depends(verify_api_key)]
)


@router.get("/verify")
async def verify_authorization():
    return {
        "success": True
    }

@router.get("/rids")
async def get_rids():
    return json_serialize(
        sensor_interface.get_rids()
    )
    
@router.get("/object")
async def get_object(
    rid: str = Query(...), 
    api_key: str = Depends(verify_api_key)
):
    rid: RID = RID.from_string(rid)
    
    bundle = sensor_interface.get_object(rid)
    if bundle is not None:
        return bundle.to_json()        

    raise HTTPException(
        status_code=404,
        detail="RID not found"
    )

@router.post("/events/subscribe")
async def subscribe_to_events():
    subscriber_id = coordinator_interface.register_subscriber()
    return {
        "subscriber_id": subscriber_id
    }
    
@router.get("/events/poll/{subscriber_id}")
async def poll_events(subscriber_id: str):
    events = coordinator_interface.poll_events(subscriber_id)
    if events is not None:
        return json_serialize(events)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Subscriber not found"
    )
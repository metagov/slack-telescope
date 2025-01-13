from fastapi import Query, Depends, Request, HTTPException, status
from rid_lib.core import RID
from rid_lib.ext.utils import json_serialize
from app import sensor_interface, coordinator_interface
from app.core import slack_handler
from .core import fastapi_app
from .auth import verify_api_key


@fastapi_app.post("/slack/listener")
async def slack_listener(request: Request):
    return await slack_handler.handle(request)

@fastapi_app.get("/verify")
async def verify_authorization(api_key: str = Depends(verify_api_key)):
    return {
        "success": True
    }

@fastapi_app.get("/rids")
async def get_rids(api_key: str = Depends(verify_api_key)):
    return json_serialize(
        sensor_interface.get_rids()
    )
    
@fastapi_app.get("/object")
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

@fastapi_app.post("/events/subscribe")
async def subscribe_to_events(api_key: str = Depends(verify_api_key)):
    subscriber_id = coordinator_interface.register_subscriber()
    return {
        "subscriber_id": subscriber_id
    }
    
@fastapi_app.get("/events/poll/{subscriber_id}")
async def poll_events(
    subscriber_id: str,
    api_key: str = Depends(verify_api_key),
):
    events = coordinator_interface.poll_events(subscriber_id)
    if events is not None:
        return json_serialize(events)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Subscriber not found"
    )
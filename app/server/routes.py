from fastapi import Query, Depends, Request
from rid_lib.core import RID
from app import persistent
from app.export import export_msg_to_json
from app.core import slack_handler
from .core import fastapi_app
from .auth import verify_api_key


@fastapi_app.post("/slack/listener")
async def slack_listener(request: Request):
    return await slack_handler.handle(request)

@fastapi_app.get("/rids")
async def get_rids(api_key: str = Depends(verify_api_key)):
    return [
        str(rid) for rid in persistent.retrieve_all_rids(filter_accepted=True)
    ]
    
@fastapi_app.get("/object")
async def get_object(
    rid: str = Query(...), 
    api_key: str = Depends(verify_api_key)
):
    rid_obj = RID.from_string(rid)
    return export_msg_to_json(rid_obj)

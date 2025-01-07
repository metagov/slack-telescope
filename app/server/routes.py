from fastapi import Query, Depends, Request, HTTPException
from rid_lib.core import RID
from app import persistent
from app.core import effector, slack_handler
from app.rid_types import Telescoped
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
    return [
        str(rid) for rid in persistent.retrieve_all_rids(filter_accepted=True)
    ]
    
@fastapi_app.get("/object")
async def get_object(
    rid: str = Query(...), 
    api_key: str = Depends(verify_api_key)
):
    rid: RID = RID.from_string(rid)
    
    print(rid)
    
    # if isinstance(rid, Telescoped):
    bundle = effector.dereference(rid)
                    
    if bundle is not None:
        return bundle.to_json()        

    return HTTPException(
        status_code=404,
        detail="RID not found"
    )

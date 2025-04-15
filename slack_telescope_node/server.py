import json
import os
import secrets
import logging
from contextlib import asynccontextmanager

from slack_bolt.adapter.socket_mode import SocketModeHandler
from fastapi import APIRouter, FastAPI
from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security import APIKeyHeader
from koi_net.processor.knowledge_object import KnowledgeSource
from koi_net.protocol.api_models import (
    PollEvents,
    FetchRids,
    FetchManifests,
    FetchBundles,
    EventsPayload,
    RidsPayload,
    ManifestsPayload,
    BundlesPayload
)
from koi_net.protocol.consts import (
    BROADCAST_EVENTS_PATH,
    POLL_EVENTS_PATH,
    FETCH_RIDS_PATH,
    FETCH_MANIFESTS_PATH,
    FETCH_BUNDLES_PATH
)

from slack_telescope_node import rid_types
from slack_telescope_node.rid_types import Telescoped

from . import persistent
from .config import AUTH_JSON_PATH, SLACK_APP_TOKEN
from .core import node, slack_handler, slack_app, effector

logger = logging.getLogger(__name__)


api_key_header = APIKeyHeader(name="X-API-Key")

if not os.path.exists(AUTH_JSON_PATH):
    with open(AUTH_JSON_PATH, "w") as f:
        json.dump([secrets.token_urlsafe(32)], f)

with open(AUTH_JSON_PATH, "r") as f:
    API_KEYS = json.load(f)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key in API_KEYS:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key"
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    node.start()
    SocketModeHandler(slack_app, SLACK_APP_TOKEN).connect()
    yield
    node.stop()


app = FastAPI(lifespan=lifespan)

@app.post("/slack/listener")
async def slack_listener(request: Request):
    return await slack_handler.handle(request)


koi_net_router = APIRouter(
    prefix="/koi-net",
    dependencies=[Depends(verify_api_key)]
)

@koi_net_router.post("/verify")
async def verify_authorization():
    return {
        "success": True
    }

@koi_net_router.post(BROADCAST_EVENTS_PATH)
async def broadcast_events(req: EventsPayload):
    logger.info(f"Request to {BROADCAST_EVENTS_PATH}, received {len(req.events)} event(s)")
    for event in req.events:
        node.processor.handle(event=event, source=KnowledgeSource.External)
    

@koi_net_router.post(POLL_EVENTS_PATH)
async def poll_events(req: PollEvents) -> EventsPayload:
    logger.info(f"Request to {POLL_EVENTS_PATH}")
    events = node.network.flush_poll_queue(req.rid)
    return EventsPayload(events=events)

@koi_net_router.post(FETCH_RIDS_PATH)
async def fetch_rids(req: FetchRids) -> RidsPayload:
    rids = []
    for _rid in persistent.retrieve_all_rids(filter_accepted=True):
        rid = Telescoped(_rid)

        if not rid_types or type(rid) not in req.rid_types:
            rids.append(rid)
                    
    return RidsPayload(rids=rids)
    
@koi_net_router.post(FETCH_MANIFESTS_PATH)
async def fetch_manifests(req: FetchManifests) -> ManifestsPayload:
    return node.network.response_handler.fetch_manifests(req)

@koi_net_router.post(FETCH_BUNDLES_PATH)
async def fetch_bundles(req: FetchBundles) -> BundlesPayload:
    bundles = []
    not_found = []
    for rid in req.rids:
        bundle = effector.deref(rid)
        if bundle:
            bundles.append(bundle)
        else:
            not_found.append(rid)
            
    return BundlesPayload(bundles=bundles, not_found=not_found)
        
app.include_router(koi_net_router)
    
"""

@app.get("/rids")
async def get_rids(api_key: str = Depends(verify_api_key)):
    return json_serialize(
        sensor_interface.get_rids()
    )
    
@app.get("/manifests")
async def get_rids(api_key: str = Depends(verify_api_key)):
    return json_serialize(
        sensor_interface.get_manifests()
    )
    
@app.get("/object")
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

@app.post("/events/subscribe")
async def subscribe_to_events(api_key: str = Depends(verify_api_key)):
    subscriber_id = coordinator_interface.register_subscriber()
    return {
        "subscriber_id": subscriber_id
    }
    
@app.get("/events/poll/{subscriber_id}")
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
"""
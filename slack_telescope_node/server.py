import json
import os
import secrets
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi import Security, HTTPException, status, Query, Depends, Request
from fastapi.security import APIKeyHeader
from rid_lib.core import RID
from rid_lib.ext.utils import json_serialize
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

from . import sensor_interface, coordinator_interface
from .config import AUTH_JSON_PATH
from .core import node, slack_handler

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
    yield
    node.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/slack/listener")
async def slack_listener(request: Request):
    return await slack_handler.handle(request)


koi_net_router = APIRouter(
    prefix="/koi-net"
)

@app.get("/verify")
async def verify_authorization(api_key: str = Depends(verify_api_key)):
    return {
        "success": True
    }

####


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
    return node.network.response_handler.fetch_rids(req)

@koi_net_router.post(FETCH_MANIFESTS_PATH)
async def fetch_manifests(req: FetchManifests) -> ManifestsPayload:
    return node.network.response_handler.fetch_manifests(req)

@koi_net_router.post(FETCH_BUNDLES_PATH)
async def fetch_bundles(req: FetchBundles) -> BundlesPayload:
    return node.network.response_handler.fetch_bundles(req)

app.include_router(koi_net_router)
    
####

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
import logging
from rid_lib import RID
from rid_lib.types import KoiNetNode
from rid_lib.ext import Manifest, Cache
from rid_lib.ext.bundle import Bundle

from koi_net.protocol.api_models import (
    RidsPayload,
    ManifestsPayload,
    BundlesPayload,
    FetchRids,
    FetchManifests,
    FetchBundles,
)
from koi_net.effector import Effector
from .rid_types import Telescoped

logger = logging.getLogger(__name__)


class TelescopeResponseHandler:
    """Handles generating responses to requests from other KOI nodes."""
    
    cache: Cache
    effector: Effector
    
    def __init__(
        self, 
        cache: Cache, 
        effector: Effector,
    ):
        print("initialized custom response handler")
        self.cache = cache
        self.effector = effector
        
    def list_allowed_rids(self, rid_types: list[type[RID]]):
        if (not rid_types) or (Telescoped in rid_types):        
            return self.cache.list_rids(rid_types=[Telescoped])
        else:
            return []
        
    def fetch_rids(self, req: FetchRids, source: KoiNetNode) -> RidsPayload:
        logger.info(f"Request to fetch rids, allowed types {req.rid_types}")
        rids = self.list_allowed_rids(req.rid_types)
        return RidsPayload(rids=rids)
        
    def fetch_manifests(self, req: FetchManifests, source: KoiNetNode) -> ManifestsPayload:
        logger.info(f"Request to fetch manifests, allowed types {req.rid_types}, rids {req.rids}")
        
        manifests: list[Manifest] = []
        not_found: list[RID] = []
        
        for rid in (req.rids or self.list_allowed_rids(req.rid_types)):
            if type(rid) is not Telescoped:
                not_found.append(rid)
                continue
            
            bundle = self.effector.deref(rid)
            if bundle:
                manifests.append(bundle.manifest)
            else:
                not_found.append(rid)
        
        return ManifestsPayload(manifests=manifests, not_found=not_found)
        
    def fetch_bundles(self, req: FetchBundles, source: KoiNetNode) -> BundlesPayload:
        logger.info(f"Request to fetch bundles, requested rids {req.rids}")
        
        bundles: list[Bundle] = []
        not_found: list[RID] = []

        for rid in req.rids:
            if type(rid) is not Telescoped:
                not_found.append(rid)
                continue
            
            bundle = self.effector.deref(rid)
            if bundle:
                bundles.append(bundle)
            else:
                not_found.append(rid)
            
        return BundlesPayload(bundles=bundles, not_found=not_found)
from dataclasses import dataclass

from rid_lib import RID
from rid_lib.types import KoiNetNode
from rid_lib.ext import Manifest
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
from koi_net.network.response_handler import ResponseHandler

from .rid_types import Telescoped


@dataclass
class TelescopeResponseHandler(ResponseHandler):
    """Handles generating responses to requests from other KOI nodes."""
    
    effector: Effector
    
    def list_allowed_rids(self, rid_types: list[type[RID]]):
        if (not rid_types) or (Telescoped in rid_types):
            return self.cache.list_rids(rid_types=[Telescoped])
        else:
            return []
        
    def fetch_rids_handler(
        self, 
        req: FetchRids, 
        source: KoiNetNode
    ) -> RidsPayload:
        self.log.info(f"Request to fetch rids, allowed types {req.rid_types}")
        rids = self.list_allowed_rids(req.rid_types)
        return RidsPayload(rids=rids)
        
    def fetch_manifests_handler(
        self, 
        req: FetchManifests, 
        source: KoiNetNode
    ) -> ManifestsPayload:
        self.log.info(f"Request to fetch manifests, allowed types {req.rid_types}, rids {req.rids}")
        
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
        
    def fetch_bundles_handler(
        self, 
        req: FetchBundles, 
        source: KoiNetNode
    ) -> BundlesPayload:
        self.log.info(f"Request to fetch bundles, requested rids {req.rids}")
        
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
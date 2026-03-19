from dataclasses import dataclass
from logging import Logger

from koi_net.components import Effector
from koi_net.infra import depends_on

from .rid_types import Telescoped
from .persistent import retrieve_all_rids


@dataclass
class CacheSychronizer:
    effector: Effector
    log: Logger
    
    @depends_on("telescope_backfiller", "server")
    def start(self):
        accepted_telescopes = retrieve_all_rids(filter_accepted=True)
        self.log.info(f"Processing {len(accepted_telescopes)} telescopes")
        for rid in accepted_telescopes:
            self.effector.deref(Telescoped(rid))
from rid_lib import RID
from .rid_types import Telescoped
from .core import effector
from . import persistent
from .rid_types import Telescoped

def get_rids():
    return [
        Telescoped(rid)
        for rid in persistent.retrieve_all_rids(filter_accepted=True)
    ]
    
def get_object(rid: RID):
    if isinstance(rid, Telescoped):
        return effector.deref(rid)
        
from koi_net.processor import ProcessorInterface
from koi_net.processor.knowledge_object import KnowledgeObject
from koi_net.processor.handler import HandlerType

from .rid_types import Telescoped
from .core import node, effector


@node.processor.register_handler(HandlerType.RID, rid_types=[Telescoped])
def telescoped_handler(processor: ProcessorInterface, kobj: KnowledgeObject):
    bundle = effector.deref(kobj.rid, hit_cache=False)
    
    if bundle is None:
        return
    
    kobj.manifest = bundle.manifest
    kobj.contents = bundle.contents
    return kobj
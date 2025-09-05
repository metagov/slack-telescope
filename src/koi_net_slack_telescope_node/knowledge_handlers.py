import logging
from koi_net.processor.handler import HandlerType, STOP_CHAIN
from koi_net.processor.knowledge_object import KnowledgeObject
from koi_net.context import HandlerContext
from rid_lib.types import KoiNetNode
from .core import node

logger = logging.getLogger(__name__)


@node.pipeline.register_handler(handler_type=HandlerType.RID, rid_types=[KoiNetNode])
def trust_only_first_contact(ctx: HandlerContext, kobj: KnowledgeObject):
    if kobj.source is None:
        return
    
    # block external events about nodes not from the first contact (coordinator)
    if kobj.source != node.config.koi_net.first_contact.rid:
        logger.info("Blocking node knowledge object not sent by first contact")
        return STOP_CHAIN
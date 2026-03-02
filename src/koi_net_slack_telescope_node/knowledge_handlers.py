from koi_net.components.interfaces import KnowledgeHandler, HandlerType, STOP_CHAIN
from koi_net.protocol import KnowledgeObject
from rid_lib.types import KoiNetNode

from .config import SlackTelescopeNodeConfig


class TrustOnlyFirstContact(KnowledgeHandler):
    config: SlackTelescopeNodeConfig
    
    handler_type=HandlerType.RID
    rid_types=(KoiNetNode,)

    def handle(self, kobj: KnowledgeObject):
        if kobj.source is None:
            return
        
        # block external events about nodes not from the first contact (coordinator)
        if kobj.source != self.config.koi_net.first_contact.rid:
            self.log.info("Blocking node knowledge object not sent by first contact")
            return STOP_CHAIN
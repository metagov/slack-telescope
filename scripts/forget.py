from rid_lib.types import KoiNetNode
from koi_net_slack_telescope_node.core import node

node.lifecycle.start()
for rid in node.cache.list_rids(rid_types=[KoiNetNode]):
    node.processor.handle(rid=rid, event_type="FORGET")
node.lifecycle.stop()
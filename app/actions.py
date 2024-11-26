from rid_lib.core import RID
from .core import slack_app
from .constants import BlockId
from . import orchestrator, utils


@slack_app.action({"block_id": BlockId.REQUEST})
def handle_request_action(ack, action):
    ack()
        
    action_id = action["action_id"]
    rid_string = utils.normalize_legacy_prefix(action["value"])
    message = RID.from_string(rid_string)
    
    orchestrator.handle_request_interaction(action_id, message)
     

@slack_app.action({"block_id": BlockId.CONSENT})
def handle_consent_action(ack, action):
    ack()
    
    action_id = action["action_id"]
    rid_string = utils.normalize_legacy_prefix(action["value"])
    message = RID.from_string(rid_string)
    
    orchestrator.handle_consent_interaction(action_id, message)
        
        
@slack_app.action({"block_id": BlockId.RETRACT})
def handle_retract_action(ack, action):
    ack()
    
    action_id = action["action_id"]
    rid_string = utils.normalize_legacy_prefix(action["value"])
    message = RID.from_string(rid_string)
    
    orchestrator.handle_retract_interaction(action_id, message)
    
    
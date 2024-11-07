from rid_lib.core import RID
from rid_lib.types import SlackUser
from app import orchestrator
from app.dereference import deref
import json, time

with open("backfill.json", "r") as f:
    data = json.load(f)
    
    for channel_id, channel in data.items():
        if channel["observed_messages"] == 0:
            continue
        
        for message_str in channel["messages"]:
            message = RID.from_string(message_str)
            message_data = deref(message)
            
            author_user_id = message_data["user"]
            
            for reaction in message_data["reactions"]:
                if reaction["name"] == "telescope":
                    tagger_user_id = reaction["users"][0]
                    break
            
            author = SlackUser(message.workspace_id, author_user_id)
            tagger = SlackUser(message.workspace_id, tagger_user_id)
                        
            orchestrator.create_request_interaction(message, author, tagger)
            time.sleep(1)
from rid_lib.core import RID
from rid_lib.types import SlackUser
from app import orchestrator
from app.core import effector
from app.config import TELESCOPE_EMOJI
import json, time

messages = []
with open("backfill.json", "r") as f:
    data = json.load(f)
    
    for channel_id, channel in data.items():
        if channel["observed_messages"] == 0:
            continue
        
        messages.extend([RID.from_string(msg_str) for msg_str in channel["messages"]])
        
        
messages.sort(key=lambda x: x.ts)
for i, message in enumerate(messages):
    message_data = effector.dereference(message).contents
    
    print(message_data)
    
    author_user_id = message_data["user"]
    
    for reaction in message_data["reactions"]:
        if reaction["name"] == TELESCOPE_EMOJI:
            tagger_user_id = reaction["users"][0]
            break
    
    author = SlackUser(message.team_id, author_user_id)
    tagger = SlackUser(message.team_id, tagger_user_id)
    
    print(i, "/", len(messages), end=" ")
    orchestrator.create_request_interaction(message, author, tagger)
    time.sleep(1)
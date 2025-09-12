from rid_lib.core import RID
from rid_lib.types import SlackUser
from koi_net_slack_telescope_node import orchestrator
from koi_net_slack_telescope_node.core import node
import json, time

def dispatch_messages():
    messages = []
    with open("backfill.json", "r") as f:
        data = json.load(f)
        
        for channel_id, channel in data.items():
            if channel["observed_messages"] == 0:
                continue
            
            messages.extend([RID.from_string(msg_str) for msg_str in channel["messages"]])
            
            
    messages.sort(key=lambda x: x.ts)
    for i, message in enumerate(messages):
        message_data = node.effector.deref(message).contents
                
        author_user_id = message_data["user"]
        
        for reaction in message_data["reactions"]:
            if reaction["name"] == node.config.telescope.emoji:
                tagger_user_id = reaction["users"][0]
                break
        
        author = SlackUser(message.team_id, author_user_id)
        tagger = SlackUser(message.team_id, tagger_user_id)
        
        print(i, "/", len(messages), end=" ")
        orchestrator.create_request_interaction(message, author, tagger)
        time.sleep(1)

if __name__ == "__main__":
    node.lifecycle.start()
    dispatch_messages()
    node.lifecycle.stop()
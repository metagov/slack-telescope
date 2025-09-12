import os, shutil
from koi_net_slack_telescope_node.utils import decode_b64, encode_b64

shutil.copytree("persistent", "persistent_backup")

for file_name in os.listdir("persistent"):
    encoded_name = file_name.split(".")[0]
    original_rid_string = decode_b64(encoded_name)
    new_rid_string = original_rid_string.replace("ori:", "orn:")
    
    with open(f"persistent_backup/{file_name}", "r") as f:
        content = f.read()
        
    updated_content = content.replace("ori:", "orn:")
    new_file_name = encode_b64(new_rid_string) + ".json"
    
    os.remove(f"persistent/{file_name}")
    
    with open(f"persistent/{new_file_name}", "w") as f:
        f.write(updated_content)
    

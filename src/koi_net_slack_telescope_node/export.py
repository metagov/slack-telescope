import csv, os, time, json
from .rid_types import Telescoped
from .persistent import retrieve_all_rids
from .core import node


def export_msgs_to_csv():
    msgs = []
    for msg_rid in retrieve_all_rids(filter_accepted=True):
        bundle = node.effector.deref(Telescoped(msg_rid))
        if bundle is not None:
            msg_json = bundle.contents
        if msg_json is not None:
            msgs.append(msg_json)

    if not os.path.exists("export"):
        os.makedirs("export")

    timestamp = str(time.time()).replace(".", "_")
    filename = f"export/{timestamp}.csv"
    
    f = open(filename, "w", encoding="utf-8", newline="")
    writer = csv.writer(f)
    
    json_keys = list(msgs[0].keys())

    writer.writerow(json_keys)

    for msg_json in msgs:
        try:
            writer.writerow([
                ";".join(msg_json[k])
                if isinstance(msg_json[k], list) 
                else msg_json[k]
                for k in json_keys
            ])
        except UnicodeEncodeError:
            with open("failed_export.json", "w") as f:
                json.dump(msg_json, f, indent=2)
            print("failed, dumping json")
            quit()
        
    return filename

if __name__ == "__main__":
    export_msgs_to_csv()
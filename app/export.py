import csv, os, time, json
from datetime import datetime, timezone
from rid_lib.types import HTTPS, SlackMessage, SlackChannel, SlackWorkspace
from .dereference import deref, transform
from .persistent import PersistentMessage, retrieve_all_rids
from .constants import MessageStatus
from .utils import retraction_time_elapsed, encode_b64

def format_timestamp(ts):
    return datetime.fromtimestamp(
        float(ts), timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%S")

def export_msg_to_json(msg: SlackMessage):
    p_msg = PersistentMessage(msg)
    
    if p_msg.status not in (MessageStatus.ACCEPTED, MessageStatus.ACCEPTED_ANON):
        return None
    
    message_data = deref(msg)
    channel_data = deref(SlackChannel(msg.team_id, msg.channel_id))
    team_data = deref(SlackWorkspace(msg.team_id))
    author_data = deref(p_msg.author)
    tagger_data = deref(p_msg.tagger)
    
    message_in_thread = msg.ts != message_data.get("thread_ts", msg.ts)
    edited_timestamp = message_data.get("edited", {}).get("ts")
    edited_at = format_timestamp(edited_timestamp) if edited_timestamp else None
    created_at = format_timestamp(msg.ts)
    
    if p_msg.status == MessageStatus.ACCEPTED:
        author_user_id = p_msg.author.user_id
        author_name = author_data.get("real_name")
        anonymous = False
        
    elif p_msg.status == MessageStatus.ACCEPTED_ANON:
        author_user_id = None
        author_name = None
        anonymous = True
        
    # extract keys from emojis if num reactions > 0
    emojis = [
        k for k, v in p_msg.emojis.items()
        if v > 0
    ] if p_msg.emojis else []
    
    msg_url = transform(msg, HTTPS)
    
    msg_json = {
        "message_rid": str(msg),
        "team_id": msg.team_id,
        "team_name": team_data["name"],
        "channel_id": msg.channel_id,
        "channel_name": channel_data["name"],
        "timestamp": msg.ts,
        "text": message_data.get("text", ""),
        "thread_timestamp": message_data.get("thread_ts"),
        "message_in_thread": message_in_thread,
        "created_at": created_at,
        "edited_at": edited_at,
        "author_user_id": author_user_id,
        "author_name": author_name,
        "tagger_user_id": p_msg.tagger.user_id,
        "tagger_name": tagger_data.get("real_name"),
        "author_is_anonymous": anonymous,
        "emojis": emojis,
        "comments": p_msg.comments or [],
        "retraction_time_elapsed": retraction_time_elapsed(p_msg),
        "permalink": msg_url
    }
    
    return msg_json
    

def export_msgs_to_json():
    rids = retrieve_all_rids(filter_accepted=True)
    message_rids = [rid for rid in rids if type(rid) == SlackMessage]
    
    msgs = []
    for msg in message_rids:
        msg_json = export_msg_to_json(msg)
        if msg_json is not None:
            msgs.append(msg_json)
            
    return msgs


def export_msgs_to_csv():
    messages_json = export_msgs_to_json()

    if not os.path.exists("export"):
        os.makedirs("export")

    timestamp = str(time.time()).replace(".", "_")
    filename = f"export/{timestamp}.csv"
    
    f = open(filename, "w", encoding="utf-8", newline="")
    writer = csv.writer(f)

    writer.writerow([
        "message_rid",
        "team_id",
        "team_name",
        "channel_id",
        "channel_name",
        "timestamp",
        "text",
        "thread_timestamp",
        "message_in_thread",
        "created_at",
        "edited_at",
        "author_user_id",
        "author_name",
        "tagger_user_id",
        "tagger_name",
        "author_is_anonymous",
        "emojis",
        "comments",
        "retraction_time_elapsed",
        "permalink"
    ])

    for msg_json in messages_json:
        try:
            writer.writerow([
                msg_json["message_rid"],
                msg_json["team_id"],
                msg_json["team_name"],
                msg_json["channel_id"],
                msg_json["channel_name"],
                msg_json["timestamp"],
                msg_json["text"],
                msg_json["thread_timestamp"],
                msg_json["message_in_thread"],
                msg_json["created_at"],
                msg_json["edited_at"],
                msg_json["author_user_id"],
                msg_json["author_name"],
                msg_json["tagger_user_id"],
                msg_json["tagger_name"],
                msg_json["author_is_anonymous"],
                ";".join(msg_json["emojis"]),
                ";".join(msg_json["comments"]),
                msg_json["retraction_time_elapsed"],
                msg_json["permalink"]
            ])
        except UnicodeEncodeError:
            with open("failed_export.json", "w") as f:
                json.dump(msg_json, f, indent=2)
            print("failed, dumping json")
            quit()
        
    return filename

if __name__ == "__main__":
    export_msgs_to_csv()
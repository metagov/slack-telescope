import csv, os, time
from datetime import datetime, timezone
from rid_lib.types import HTTPS, SlackMessage, SlackChannel
from .dereference import deref, transform
from .persistent import PersistentMessage, retrieve_all_rids
from .constants import MessageStatus
from .utils import retraction_time_elapsed


def export_to_csv():
    rids = retrieve_all_rids()
    message_rids = [rid for rid in rids if type(rid) == SlackMessage ]

    if not os.path.exists("export"):
        os.makedirs("export")

    timestamp = str(time.time()).replace(".", "_")
    filename = f"export/{timestamp}.csv"
    
    f = open(filename, "w", newline="")
    writer = csv.writer(f)

    writer.writerow([
        "message_rid",
        "text",
        "channel_name",
        "message_url",
        "author_rid",
        "author_name",
        "anonymous",
        "in_thread",
        "thread_rid",
        "created_at",
        "tagger_rid",
        "tagger_name",
        "retraction_time_elapsed",
        "emojis",
        "comments"
    ])

    for msg in message_rids:
        p_msg = PersistentMessage(msg)
        
        if p_msg.status not in (MessageStatus.ACCEPTED, MessageStatus.ACCEPTED_ANON):
            continue
        
        message_data = deref(msg)
        channel = SlackChannel(msg.team_id, msg.channel_id)
        channel_data = deref(channel)
        author_data = deref(p_msg.author)
        tagger_data = deref(p_msg.tagger)
        msg_url = transform(msg, HTTPS)
        
        if p_msg.emojis:
            emojis = ";".join([
                k for k, v in p_msg.emojis.items()
                if v > 0
            ])
        else:
            emojis = ""
        
        if p_msg.comments:
            comments = ";".join(p_msg.comments)
        else:
            comments = ""
        
        in_thread = msg.ts != message_data.get("thread_ts", msg.ts)
        
        created_at = datetime.fromtimestamp(
            float(msg.ts), timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S")
        
        if p_msg.status == MessageStatus.ACCEPTED:
            author_rid = str(p_msg.author)
            author_name = author_data.get("real_name")
            anonymous = False
            
        elif p_msg.status == MessageStatus.ACCEPTED_ANON:
            author_rid = None
            author_name = None
            anonymous = True
        
        writer.writerow([
            str(msg),
            message_data.get("text"),
            channel_data.get("name"),
            str(msg_url),
            author_rid,
            author_name,
            anonymous,
            in_thread,
            message_data.get("thread_ts"),
            created_at,
            str(p_msg.tagger),
            tagger_data.get("real_name"),
            retraction_time_elapsed(p_msg),
            emojis,
            comments
        ])
        
    return filename

if __name__ == "__main__":
    export_to_csv()
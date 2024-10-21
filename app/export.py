import csv, os, time
from datetime import datetime, timezone
from rid_lib.types import HTTPS
from .core import graph
from .dereference import deref, transform
from .persistent import PersistentMessage
from .constants import MessageStatus


def export_to_csv():
    messages = graph.read_all()

    if not os.path.exists("export"):
        os.makedirs("export")

    timestamp = str(time.time()).replace(".", "_")
    filename = f"export/{timestamp}.csv"
    
    f = open(filename, "w", newline="")
    writer = csv.writer(f)

    writer.writerow([
        "message_rid",
        "message_url",
        "author_rid",
        "author_name",
        "anonymous",
        "created_at",
        "tagger_rid",
        "tagger_name"
    ])

    for msg in messages:
        p_msg = PersistentMessage(msg)
        
        author_data = deref(p_msg.author)
        tagger_data = deref(p_msg.tagger)
        msg_url = transform(msg, HTTPS)
        created_at = datetime.fromtimestamp(
            float(msg.message_id), timezone.utc
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
            str(msg_url),
            author_rid,
            author_name,
            anonymous,
            created_at,
            str(p_msg.tagger),
            tagger_data.get("real_name")
        ])
        
    return filename
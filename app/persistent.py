import json, os
from rid_lib.core import RID
from rid_lib.types import SlackMessage, SlackUser, HTTPS
from .config import PERSISTENT_DIR
from .constants import UserStatus, MessageStatus
from .utils import encode_b64, decode_b64


class PersistentObject:
    _directory = PERSISTENT_DIR
    _instances = {}
    
    # ensures same RID results in same object
    def __new__(cls, rid: RID):
        if str(rid) not in cls._instances:
            inst = super().__new__(cls)
            cls._instances[str(rid)] = inst
        return cls._instances[str(rid)]
    
    def __init__(self, rid: RID, default_data: dict = {}):
        self.rid = rid
        self._data = self._read() or default_data
        self._data["rid"] = str(rid)
        # self._write()
        
    @property
    def _file_path(self):
        encoded_rid_str = encode_b64(str(self.rid))
        return f"{self._directory}/{encoded_rid_str}.json"
    
    def _read(self):
        try:
            with open(self._file_path, "r") as f:
                return json.load(f)

        except FileNotFoundError:
            return None
    
    def _write(self):
        if not os.path.exists(self._directory):
            os.makedirs(self._directory)
            
        with open(self._file_path, "w") as f:
            json.dump(self._data, f, indent=2)
            
    
def persistent_prop(attribute, rid=False):
    def getter(self: PersistentObject):
        value = self._data.get(attribute)
        if value:
            return RID.from_string(value) if rid else value
    
    def setter(self: PersistentObject, value):
        self._data[attribute] = str(value) if rid else value
        self._write()
    
    return property(getter, setter)


class PersistentUser(PersistentObject):
    _instances = {}
    
    status = persistent_prop("status")
    msg_queue = persistent_prop("msg_queue")
    
    def __init__(self, rid: RID):
        super().__init__(rid, {
            "status": UserStatus.UNSET,
            "msg_queue": []
        })
    
    def enqueue(self, obj):
        self._data["msg_queue"].append(str(obj))
        self._write()
        
    def dequeue(self):
        elem = self._data["msg_queue"].pop(0)
        self._write()
        return RID.from_string(elem)
    

class PersistentMessage(PersistentObject):
    _instances = {}
    
    status: SlackUser = persistent_prop("status")
    author: SlackUser = persistent_prop("author", rid=True)
    tagger: SlackUser = persistent_prop("tagger", rid=True)
    
    request_interaction: SlackMessage = persistent_prop("request_interaction", rid=True)
    consent_interaction: SlackMessage = persistent_prop("consent_interaction", rid=True)
    retract_interaction: SlackMessage = persistent_prop("retract_interaction", rid=True)
    broadcast_interaction: SlackMessage = persistent_prop("broadcast_interaction", rid=True)
    permalink: HTTPS = persistent_prop("permalink", rid=True)
    
    comments: list[str] = persistent_prop("comments")
    emojis: list[str] = persistent_prop("emojis")
    
    def __init__(self, rid: RID):
        super().__init__(rid, {
            "status": MessageStatus.UNSET
        })
        
    def add_comment(self, comment: str):
        self._data.setdefault("comments", []).append(comment)
        self._write()
        
    def add_emoji(self, emoji_str: str):
        emojis = self._data.setdefault("emojis", {})
        emojis[emoji_str] = emojis.get(emoji_str, 0) + 1
        self._write()
    
    def remove_emoji(self, emoji_str: str):
        emojis = self._data.setdefault("emojis", {})
        emojis[emoji_str] = max(emojis.get(emoji_str, 0) - 1, 0)
        if emojis[emoji_str] == 0:
            del emojis[emoji_str]
        self._write()
        return emojis.get(emoji_str, 0)
        
class PersistentRequestLink(PersistentObject):
    _instances = {}
    
    message = persistent_prop("message", rid=True)

    def __init__(self, rid: RID):
        super().__init__(rid, {
            "status": None
        })

def create_link(request_interaction, message):
    PersistentRequestLink(request_interaction).message = message
    
def get_linked_message(request_interaction):
    return PersistentRequestLink(request_interaction).message
        

def retrieve_all_rids(filter_accepted=False):
    if not os.path.exists(PERSISTENT_DIR):
        return []
    
    rids = [
        RID.from_string(
            decode_b64(
                fname.removesuffix(".json")
            )
        ) for fname in os.listdir(PERSISTENT_DIR)
    ]
    
    if not filter_accepted:
        return rids
    
    filtered_rids = []
    for rid in rids:
        if PersistentMessage(rid).status in (MessageStatus.ACCEPTED, MessageStatus.ACCEPTED_ANON):
            filtered_rids.append(rid)
            
    return filtered_rids
import json, os
from rid_lib.core import RID
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
        self._write()
        
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
        value = self._data[attribute]
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
    
    status = persistent_prop("status")
    author = persistent_prop("author", rid=True)
    tagger = persistent_prop("tagger", rid=True)
    
    request_interaction = persistent_prop("request_interaction", rid=True)
    consent_interaction = persistent_prop("consent_interaction", rid=True)
    retract_interaction = persistent_prop("retract_interaction", rid=True)
    broadcast_interaction = persistent_prop("broadcast_interaction", rid=True)
    permalink = persistent_prop("permalink", rid=True)
    
    comments = persistent_prop("comments")
    
    def __init__(self, rid: RID):
        super().__init__(rid, {
            "status": MessageStatus.UNSET,
            "comments": []
        })
        
    def add_comment(self, comment: str):
        self._data["comments"].append(comment)
        self._write()
        
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
        

def retrieve_all_rids():
    return [
        RID.from_string(
            decode_b64(
                fname.removesuffix(".json")
            )
        ) for fname in os.listdir(PERSISTENT_DIR)
    ]
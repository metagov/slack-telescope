import json, os
from rid_lib.core import RID
from .config import PERSISTENT_DIR
from .utils import encode_b64


class PersistentUser:
    _directory = PERSISTENT_DIR
    
    def __init__(self, rid: RID):
        self.rid = rid
        self._data = self._read() or {
            "status": None,
            "msg_queue": []
        }
        
    @property
    def _file_path(self):
        encoded_rid_str = encode_b64(str(self.rid))
        return f"{self._directory}/{encoded_rid_str}.json"
    
    @property
    def status(self):
        return self._data["status"]

    @status.setter
    def status(self, value):
        self._data["status"] = value
        self._write()
        
    @property
    def msg_queue(self):
        return self._data["msg_queue"]
    
    def enqueue(self, rid: RID):
        self._data["msg_queue"].append(str(rid))
        self._write()
        
    def dequeue(self):
        elem = self._data["msg_queue"].pop(0)
        self._write()
        return RID.from_string(elem)
        
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
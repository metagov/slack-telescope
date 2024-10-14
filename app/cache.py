import os, json, shutil, time
from dataclasses import dataclass
from rid_lib.core import RID

from .config import CACHE_DIR
from .utils import encode_b64, hash_json


@dataclass
class CacheObject:
    """Object representing an individual RID cache entry.

    A container object for the cached data associated with an RID. It is 
    returned by the read and write functions of a CacheInterface. It 
    stores the JSON data associated with an RID object and corresponding
    metadata.
    """
    data: dict
    meta: dict
    
    @classmethod
    def from_dict(cls, json_object):
        return cls(
            json_object.get("data"),
            json_object.get("meta")
        )

    def to_dict(self): return {
            "meta": self.meta,
            "data": self.data,
        }


class CacheInterface:
    def __init__(self, directory):
        self.directory = directory
        
    def file_path(self, rid: RID):
        encoded_rid_str = encode_b64(str(rid))
        return f"{self.directory}/{encoded_rid_str}.json"

    def write(self, rid: RID, data: dict) -> CacheObject:
        """Writes a DataObject to RID cache.

        If inputted DataObject has JSON data, it is written to the cache
        directory (default 'cache/') as a JSON file with the name set to
        the base 64 encoding of the RID string.

        If inputted DataObject has files, they are written to a
        directory named with the encoded RID string (see above).

        Returns a CacheObject.
        """

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        cache_entry = CacheObject(
            data=data,
            meta={
                "rid": str(rid),
                "timestamp": time.time(),
                "sha256_hash": hash_json(data),
            }
        )

        with open(self.file_path(rid), "w") as f:
            json.dump(cache_entry.to_dict(), f, sort_keys=True, indent=2)

        return cache_entry

    def read(self, rid: RID):
        """Reads and returns CacheObject from RID cache."""
        try:
            with open(self.file_path(rid), "r") as f:
                return CacheObject.from_dict(json.load(f))
        except FileNotFoundError:
            return None
        
    def delete(self, rid: RID):
        """Deletes RID cache entry and associated files."""
        try:
            os.remove(self.file_path(rid))
        except FileNotFoundError:
            return

    def drop(self):
        """Deletes all RID cache entries."""
        try:
            shutil.rmtree(CACHE_DIR)
        except FileNotFoundError:
            return
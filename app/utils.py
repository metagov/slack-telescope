import hashlib, json
from datetime import datetime, timezone
from base64 import urlsafe_b64encode, urlsafe_b64decode
from rid_lib.core import RID
from .config import RETRACTION_TIME_LIMIT


def encode_b64(string: str):
    return urlsafe_b64encode(
        string.encode()).decode().rstrip("=")

def decode_b64(string: str):
    return urlsafe_b64decode(
        (string + "=" * (-len(string) % 4)).encode()).decode()
    
def hash_json(data: dict):
    json_bytes = json.dumps(data, sort_keys=True).encode()
    hash = hashlib.sha256()
    hash.update(json_bytes)
    return hash.hexdigest()

def normalize_legacy_prefix(rid_string: str):
    if rid_string.startswith("ori:"):
        return "orn:" + rid_string[4:]
    else:
        return rid_string

def rid_params(rid: RID):
    return {
        "scheme": rid.scheme,
        "space": rid.space,
        "form": rid.form,
        "obj_type": rid.obj_type,
        "context": rid.context
    }
    
def retraction_time_elapsed(p_message):
    initial_date = datetime.fromtimestamp(
        float(p_message.retract_interaction.ts),
        timezone.utc
    )
    
    elapsed_time = datetime.now(timezone.utc) - initial_date
    
    return elapsed_time > RETRACTION_TIME_LIMIT


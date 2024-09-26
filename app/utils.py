import hashlib
from base64 import urlsafe_b64encode, urlsafe_b64decode
from .config import TEXT_PREVIEW_CHAR_LIMIT


def truncate_text(string: str):
    if len(string) > TEXT_PREVIEW_CHAR_LIMIT:
        return string[:TEXT_PREVIEW_CHAR_LIMIT] + "..."
    else:
        return string

def indent_text(string: str):
    return "\n".join(["> " + line for line in string.splitlines()])

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
import hashlib, json, re
from base64 import urlsafe_b64encode, urlsafe_b64decode
from rid_lib.core import RID
from rid_lib.types import SlackUser, SlackMessage

from .config import TEXT_PREVIEW_CHAR_LIMIT
from .dereference import deref
 

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

def load_rid_from_json(d: dict):
    return {
        k: RID.from_string(v)
        for k, v in d.items()
    }
    
def rid_params(rid: RID):
    return {
        "scheme": rid.scheme,
        "space": rid.space,
        "form": rid.form,
        "obj_type": rid.obj_type,
        "context": rid.context
    }
    
def truncate_text(string: str):
    print(string)
    if len(string) > TEXT_PREVIEW_CHAR_LIMIT:
        return string[:TEXT_PREVIEW_CHAR_LIMIT] + "..."
    else:
        return string

def indent_text(string: str):
    return "\n".join([
        "&gt;" + line if line.startswith(("> ", "&gt; ")) else "&gt; " + line
        for line in string.splitlines()  
    ])

def filter_text(string: str):
    # replaces all @mentions
    def replace_match(match):
        try:
            user_data = deref(SlackUser("", match.group(1)))
            if not user_data or type(user_data) != dict:
                return match.group(0)
            else:
                return "@" + user_data.get("real_name")
        except Exception:
            return match.group(0)
    
    return re.sub(r"<@(\w+)>", replace_match, string)
   
def format_msg(msg: SlackMessage):
    return indent_text(
        filter_text(
            truncate_text(
                deref(msg)["text"])))
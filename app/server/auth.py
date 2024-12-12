import json, os, secrets
from app.config import AUTH_JSON_PATH
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

if not os.path.exists(AUTH_JSON_PATH):
    with open(AUTH_JSON_PATH, "w") as f:
        json.dump([
            secrets.token_urlsafe(32)
        ], f)

with open(AUTH_JSON_PATH, "r") as f:
    API_KEYS = json.load(f)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key in API_KEYS:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key"
    )
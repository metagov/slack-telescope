from fastapi import FastAPI, Request
from app.core import slack_handler
from .routes import router

fastapi_app = FastAPI()

@fastapi_app.post("/slack/listener")
async def slack_listener(request: Request):
    return await slack_handler.handle(request)

fastapi_app.include_router(router)
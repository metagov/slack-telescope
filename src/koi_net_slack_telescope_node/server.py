from dataclasses import dataclass

from koi_net.entrypoints import NodeServer
from fastapi import Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler


@dataclass
class SlackTelescopeNodeServer(NodeServer):
    slack_app: App
    
    def __post_init__(self):
        super().__post_init__()
        
        @self.app.post("/slack-event-listener")
        async def slack_listener(request: Request):
            return await SlackRequestHandler(self.slack_app).handle(request)
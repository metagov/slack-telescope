from dataclasses import dataclass, field
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import SlackTelescopeNodeConfig


@dataclass
class SlackSocketMode:
    slack_app: App
    config: SlackTelescopeNodeConfig
    handler: SocketModeHandler | None = field(init=False, default=None)
    
    def start(self):
        self.handler = SocketModeHandler(
            app=self.slack_app, 
            app_token=self.config.env.slack_app_token)
        self.handler.connect()
        
    def stop(self):
        if self.handler:
            self.handler.close()
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .config import SlackTelescopeNodeConfig


class SlackSocketMode:
    def __init__(self, slack_app: App, config: SlackTelescopeNodeConfig):
        self.handler = SocketModeHandler(slack_app, config.env.slack_app_token)
    
    def start(self):
        self.handler.connect()
        
    def stop(self):
        self.handler.close()
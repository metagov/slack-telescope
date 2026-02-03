from dataclasses import dataclass
from logging import Logger

from koi_net.secure_manager import ConfigProvider
from slack_bolt import App

from .config import SlackTelescopeNodeConfig


@dataclass
class MetaConfigHandler:
    slack_app: App
    config: SlackTelescopeNodeConfig | ConfigProvider
    log: Logger
    
    def start(self):
        resp = self.slack_app.client.auth_test()
        team_id = resp.get("team_id")
        user_id = resp.get("user_id")
        
        if not team_id or not user_id:
            raise RuntimeError("Slack auth test failed")
        
        self.config.telescope.bot_user_id = user_id
        self.config.telescope.team_id = team_id
        self.config.save_to_yaml()
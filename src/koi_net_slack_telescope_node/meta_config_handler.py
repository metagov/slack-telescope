import threading
from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from slack_bolt import App
from koi_net.components import ConfigProvider
from slack_sdk import WebClient
from .persistent import PersistentObject
from .config import SlackTelescopeNodeConfig


@dataclass
class MetaConfigHandler:
    log: Logger
    root_dir: Path
    slack_app: App
    slack_user_client: WebClient
    config: SlackTelescopeNodeConfig | ConfigProvider
    shutdown_signal: threading.Event
    
    def start(self):
        bot_auth = self.slack_app.client.auth_test()
        self.log.info(f"Connected to {bot_auth.get('team')} as {bot_auth.get('user')}")
        team_id = bot_auth.get("team_id")
        bot_user_id = bot_auth.get("user_id")
        
        user_auth = self.slack_user_client.auth_test()
        self.log.info(f"Logged in as {user_auth.get('user')}")
        admin_user_id = user_auth.get("user_id")
        
        if not team_id or not bot_user_id:
            raise RuntimeError("Slack bot auth test failed")
        
        if not admin_user_id:
            raise RuntimeError("User auth test failed")
        
        self.config.telescope.admin_user_id = admin_user_id
        self.config.telescope.bot_user_id = bot_user_id
        self.config.telescope.team_id = team_id
        self.config.save_to_yaml()
        
        PersistentObject._directory = self.root_dir / self.config.telescope.persistent_dir

        # disabling, can be set via slack command now
        # if (not self.config.telescope.observatory_channel_id) or (not self.config.telescope.broadcast_channel_id):
        #     self.log.error("Missing required config: '/telescope/observatory_channel_id`, `/telescope/broadcast_channel_id`")
        #     self.shutdown_signal.set()

from dataclasses import dataclass
from logging import Logger
import threading

from koi_net.secure_manager import ConfigProvider
from slack_bolt import App

from .persistent import PersistentObject

from .config import SlackTelescopeNodeConfig


@dataclass
class MetaConfigHandler:
    log: Logger
    slack_app: App
    config: SlackTelescopeNodeConfig | ConfigProvider
    shutdown_signal: threading.Event
    
    def start(self):
        resp = self.slack_app.client.auth_test()
        self.log.info(f"Connected to {resp.get('team')}")
        team_id = resp.get("team_id")
        user_id = resp.get("user_id")
        
        if not team_id or not user_id:
            raise RuntimeError("Slack auth test failed")
        
        self.config.telescope.bot_user_id = user_id
        self.config.telescope.team_id = team_id
        self.config.save_to_yaml()
        
        PersistentObject._directory = self.config.telescope.persistent_dir
        
        if (not self.config.telescope.observatory_channel_id) or (not self.config.telescope.broadcast_channel_id):
            self.log.error("Missing required config: '/telescope/observatory_channel_id`, `/telescope/broadcast_channel_id`")
            self.shutdown_signal.set()
            
        if (not self.config.telescope.allowed_channels):
            self.log.warning("There are no allowed channels set, messages will be unable to be processed")
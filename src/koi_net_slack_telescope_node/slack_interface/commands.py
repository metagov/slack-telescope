from dataclasses import dataclass
from logging import Logger
import threading

from koi_net.components import ConfigProvider
from slack_bolt import App
from slack_sdk.errors import SlackApiError
from ..config import SlackTelescopeNodeConfig
from ..export import Exporter


@dataclass
class SlackCommandHandler:
    log: Logger
    slack_app: App
    exporter: Exporter
    config: SlackTelescopeNodeConfig | ConfigProvider
    begin_backfill: threading.Event
    
    def __post_init__(self):
        self.register_handlers()
    
    def register_handlers(self):
        # self.slack_app.command("/export_csv")(self.handle_export_command)
        self.slack_app.command("/ping")(self.handle_ping)
        self.slack_app.command("/set-observatory-channel")(self.handle_set_observatory)
        self.slack_app.command("/set-broadcast-channel")(self.handle_set_broadcast)
        self.slack_app.command("/join-public-channels")(self.handle_join_public_channels)
        self.slack_app.command("/start-backfill")(self.handle_backfill)
        
    def join_channel(self, channel_id: str) -> bool:
        try:
            self.slack_app.client.conversations_join(channel=channel_id)
            return True
        except SlackApiError as err:
            error = err.response["error"]
            if error == "already_in_channel":
                return True
            return False
        
    def handle_backfill(self, ack, respond):
        ack()
        
        self.begin_backfill.set()
        
        respond("Started backfill!")
        
    def handle_join_public_channels(self, ack, respond):
        ack()
        
        channels = self.slack_app.client.conversations_list().get("channels")
        if not channels:
            respond("Couldn't find any channels to join")
            return
        
        respond("Searching channels...")
        joined = 0
        for channel in channels:
            try:
                resp = self.slack_app.client.conversations_join(channel=channel["id"])
                if resp.get("warning") == "already_in_channel":
                    continue
                print(f"Joined #{channel['name']}")
                joined += 1
            except SlackApiError:
                continue
        
        if joined:
            respond(f"Joined {joined} new channels!")
        else: 
            respond("Couldn't find any new channels to join")

    def handle_set_observatory(self, ack, command, respond):
        ack()

        if command["user_id"] != self.config.telescope.admin_user_id:
            respond("Sorry, you're not authorized to run this command :/")
            return

        channel_id = command["channel_id"]
        if not self.join_channel(channel_id):
            respond(text=f"Failed to join <#{channel_id}>, make sure I'm invited to the channel")
            return

        self.config.telescope.observatory_channel_id = channel_id
        self.config.save_to_yaml()
        respond(text=f"Set observatory channel to <#{channel_id}>")

    def handle_set_broadcast(self, ack, command, respond):
        ack()

        if command["user_id"] != self.config.telescope.admin_user_id:
            respond("Sorry, you're not authorized to run this command :/")
            return

        channel_id = command["channel_id"]
        if not self.join_channel(channel_id):
            respond(text=f"Failed to join <#{channel_id}>, make sure I'm invited to the channel")
            return

        self.config.telescope.broadcast_channel_id = channel_id
        self.config.save_to_yaml()
        respond(text=f"Set broadcast channel to <#{channel_id}>")

    def handle_export_command(self, ack, command, say):
        ack()
        
        self.slack_app.client.chat_postMessage(
            channel=command["channel_id"],
            text="Beginning export... (this might take a few moments!)"
        )
        
        filename = self.exporter.export_msgs_to_csv()
            
        self.slack_app.client.files_upload_v2(
            file=filename,
            filename="export.csv",
            channel=command["channel_id"],
            initial_comment="Exported data."
        )
        
    def handle_ping(self, ack, respond):
        ack()
        respond(text="Pong!")
from dataclasses import dataclass

from slack_bolt import App
from ..export import Exporter


@dataclass
class SlackCommandHandler:
    slack_app: App
    exporter: Exporter
    
    def __post_init__(self):
        self.register_handlers()
    
    def register_handlers(self):
        self.slack_app.command("/export_csv")(self.handle_export_command)
        self.slack_app.command("/ping")(self.handle_ping_command)
        
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
        
    def handle_ping_command(ack, say):
        ack()
        
        say(text="Pong!")
import os
from .core import slack_app
from .export import export_msgs_to_csv


@slack_app.command("/export_csv")
def handle_export_command(ack, command, say):
    ack()
    
    slack_app.client.chat_postMessage(
        channel=command["channel_id"],
        text="Beginning export... (this might take a few moments!)"
    )
    
    filename = export_msgs_to_csv()
        
    slack_app.client.files_upload_v2(
        file=filename,
        filename="export.csv",
        channel=command["channel_id"],
        initial_comment="Exported data."
    )
    
@slack_app.command("/ping")
def handle_ping_command(ack, say):
    ack()
    
    say(text="Pong!")
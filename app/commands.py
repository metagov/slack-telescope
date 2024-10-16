from .core import slack_app


@slack_app.command("/export")
def handle_export_command(ack, command):
    ack()
        
    slack_app.client.files_upload_v2(
        file="requirements.txt",
        filename="requirements.txt",
        channel=command["channel_id"],
        initial_comment="Exported data."
    )
from slack_bolt.adapter.socket_mode import SocketModeHandler

from .core import slack_app
from .config import SLACK_APP_TOKEN, OBSERVATORY_CHANNEL_ID, BROADCAST_CHANNEL_ID

from . import events, actions, commands

slack_app.client.conversations_join(channel=OBSERVATORY_CHANNEL_ID)
slack_app.client.conversations_join(channel=BROADCAST_CHANNEL_ID)

SocketModeHandler(slack_app, SLACK_APP_TOKEN).start()
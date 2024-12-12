from slack_bolt.adapter.socket_mode import SocketModeHandler

from .slack_interface import actions, events

from .core import slack_app
from .config import SLACK_APP_TOKEN, OBSERVATORY_CHANNEL_ID, BROADCAST_CHANNEL_ID

from .slack_interface import commands

SocketModeHandler(slack_app, SLACK_APP_TOKEN).start()
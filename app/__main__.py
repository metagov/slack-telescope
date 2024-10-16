from slack_bolt.adapter.socket_mode import SocketModeHandler

from .core import slack_app
from .config import SLACK_APP_TOKEN

from . import events, actions, commands

SocketModeHandler(slack_app, SLACK_APP_TOKEN).start()
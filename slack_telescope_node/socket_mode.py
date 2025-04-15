from slack_bolt.adapter.socket_mode import SocketModeHandler
from .core import node, slack_app
from .config import SLACK_APP_TOKEN

node.start()
try:
    SocketModeHandler(slack_app, SLACK_APP_TOKEN).start()
finally:
    node.stop()
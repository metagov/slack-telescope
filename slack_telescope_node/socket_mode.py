from slack_bolt.adapter.socket_mode import SocketModeHandler
from .core import node, slack_app


node.lifecycle.start()
try:
    SocketModeHandler(slack_app, node.config.env.slack_app_token).start()
finally:
    node.lifecycle.stop()
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from .config import *
from .graph import GraphInterface
from .config import OBSERVATORY_CHANNEL_ID, BROADCAST_CHANNEL_ID
from rid_lib.types import SlackChannel, SlackUser
from rid_lib.ext import Effector, Cache

slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    raise_error_for_unhandled_request=False
)

slack_handler = SlackRequestHandler(slack_app)

cache = Cache(CACHE_DIR)
effector = Effector(cache)

# registers actions with effector
from .effector import *

if GRAPH_ENABLED:
    graph = GraphInterface(NEO4J_URI, NEO4J_AUTH, NEO4J_DB)
else:
    graph = None

resp = slack_app.client.auth_test()
team_id = resp["team_id"]

bot_user = SlackUser(team_id, resp["user_id"])
observatory_channel = SlackChannel(team_id, OBSERVATORY_CHANNEL_ID)
broadcast_channel = SlackChannel(team_id, BROADCAST_CHANNEL_ID)

# registers handlers/listeners with Slack
from .slack_interface import actions, events, commands

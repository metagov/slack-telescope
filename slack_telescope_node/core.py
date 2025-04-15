from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from rid_lib.types import SlackChannel, SlackUser
from rid_lib.ext import Effector
from koi_net import NodeInterface
from koi_net.protocol.node import NodeProfile, NodeProvides, NodeType
from .config import *
from .graph import GraphInterface
from .config import OBSERVATORY_CHANNEL_ID, BROADCAST_CHANNEL_ID, HOST, PORT
from .rid_types import Telescoped

node = NodeInterface(
    name="slack-telescope",
    profile=NodeProfile(
        base_url=f"http://{HOST}:{PORT}",
        node_type=NodeType.FULL,
        provides=NodeProvides(
            event=[Telescoped],
            state=[Telescoped]
        )
    ),
    use_kobj_processor_thread=True
)

slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    raise_error_for_unhandled_request=False
)

slack_handler = SlackRequestHandler(slack_app)

# cache = Cache(CACHE_DIR)
effector = Effector(node.cache)

# registers actions with effector
from .effector import *

from . import knowledge_handlers

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

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import Request
from rid_lib.types import SlackChannel, SlackUser
from koi_net import NodeInterface
from .config import SlackTelescopeNodeConfig
from .graph import GraphInterface
from .persistent import PersistentObject
from .custom_response_handler import TelescopeResponseHandler

node = NodeInterface(
    config=SlackTelescopeNodeConfig.load_from_yaml("config.yaml"),
    use_kobj_processor_thread=True,
    ResponseHandlerOverride=TelescopeResponseHandler
)

node.response_handler

PersistentObject._directory = node.config.telescope.persistent_dir

slack_app = App(
    token=node.config.env.slack_bot_token,
    signing_secret=node.config.env.slack_signing_secret,
    raise_error_for_unhandled_request=False
)

slack_handler = SlackRequestHandler(slack_app)

from . import effector_actions

@node.server.app.post("/slack-listener")
async def slack_listener(request: Request):
    return await slack_handler.handle(request)


# if GRAPH_ENABLED:
#     graph = GraphInterface(NEO4J_URI, NEO4J_AUTH, NEO4J_DB)
# else:
#     graph = None

resp = slack_app.client.auth_test()
team_id = resp["team_id"]

bot_user = SlackUser(team_id, resp["user_id"])

observatory_channel = SlackChannel(
    team_id=team_id, 
    channel_id=node.config.telescope.observatory_channel_id)

broadcast_channel = SlackChannel(
    team_id=team_id, 
    channel_id=node.config.telescope.broadcast_channel_id
)

# registers handlers/listeners with Slack
from .slack_interface import actions, events, commands

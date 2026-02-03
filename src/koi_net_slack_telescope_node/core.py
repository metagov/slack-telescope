from koi_net.core import FullNode
from slack_bolt import App

from .slack_interface.events import SlackEventHandler

from .socket_mode import SlackSocketMode
from .orchestrator import Orchestrator
from .effector_actions import (
    deref_slack_channel, 
    deref_slack_message,
    deref_slack_user,
    deref_slack_workspace,
    deref_telescoped)
from .knowledge_handlers import trust_only_first_contact
from .extended_handler_context import ExtendedHandlerContext
from .slack_interface.block_builder import BlockBuilder
from .meta_config_handler import MetaConfigHandler
from .slack_interface.functions import SlackFunctions
from .server import SlackTelescopeNodeServer
from .config import SlackTelescopeNodeConfig
from .response_handler import TelescopeResponseHandler
from .slack_interface.actions import SlackActionHandler
from .slack_interface.commands import SlackCommandHandler
from .export import Exporter


class SlackTelescopeNode(FullNode):
    config_schema = SlackTelescopeNodeConfig
    response_handler = TelescopeResponseHandler
    server = SlackTelescopeNodeServer
    handler_context = ExtendedHandlerContext
    
    slack_app = lambda config: App(
        token=config.env.slack_bot_token,
        signing_secret=config.env.slack_signing_secret,
        raise_error_for_unhandled_request=False
    )
    slack_event_handler = SlackEventHandler
    slack_action_handler = SlackActionHandler
    slack_command_handler = SlackCommandHandler
    slack_functions = SlackFunctions
    
    meta_config_handler = MetaConfigHandler
    block_builder = BlockBuilder
    exporter = Exporter
    orchestrator = Orchestrator
    
    socket_mode = SlackSocketMode
    
    knowledge_handlers = FullNode.knowledge_handlers + [
        trust_only_first_contact
    ]
    deref_handlers = [
        deref_slack_user,
        deref_slack_message,
        deref_slack_channel,
        deref_slack_workspace,
        deref_telescoped
    ]

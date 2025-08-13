import os
from datetime import timedelta

from pydantic import BaseModel, Field
from koi_net.config import NodeConfig, KoiNetConfig, EnvConfig
from koi_net.protocol.node import NodeProfile, NodeProvides, NodeType
from .rid_types import Telescoped


DEBUG = os.path.exists("slack_telescope_node/debug")
print("DEBUG MODE:", DEBUG)

class SlackEnvConfig(EnvConfig):
    slack_bot_token: str = "SLACK_BOT_TOKEN"
    slack_signing_secret: str = "SLACK_SIGNING_SECRET"
    slack_app_token: str = "SLACK_APP_TOKEN"

class TelescopeConfig(BaseModel):
    backfill_file: str = "backfill.json"
    persistent_dir: str = "persistent"
    emoji: str = "telescope"
    observatory_channel_id: str | None = None
    broadcast_channel_id: str | None = None
    text_preview_char_limit: int = 500
    allowed_channels: list[str] = []

class SlackTelescopeNodeConfig(NodeConfig):
    koi_net: KoiNetConfig = Field(default_factory = lambda:
        KoiNetConfig(
            node_name="slack-telescope",
            node_profile=NodeProfile(
                node_type=NodeType.FULL,
                provides=NodeProvides(
                    event=[Telescoped],
                    state=[Telescoped]
                )
            ),
        )
    )
    telescope: TelescopeConfig = Field(default_factory=TelescopeConfig)
    env: SlackEnvConfig = Field(default_factory=SlackEnvConfig)

# if DEBUG:
#     TELESCOPE_EMOJI = "eyes"
#     OBSERVATORY_CHANNEL_ID = "C081BRCFJJY"
#     BROADCAST_CHANNEL_ID = "C081BRCFJJY"
# else:
#     TELESCOPE_EMOJI = "telescope"
#     OBSERVATORY_CHANNEL_ID = "C07V8V3PJLB"
#     BROADCAST_CHANNEL_ID = "C07T2G11363"


GRAPH_ENABLED = False


NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "telescope")
NEO4J_DB = "neo4j"


RETRACTION_TIME_LIMIT = timedelta(weeks=4)
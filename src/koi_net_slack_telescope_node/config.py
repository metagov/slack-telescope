from pydantic import BaseModel, Field
from koi_net.config import (
    FullNodeConfig, 
    KoiNetConfig, 
    FullNodeProfile, 
    NodeProvides,
    EnvConfig
)
from rid_lib.types import KoiNetNode

from .rid_types import Telescoped


class SlackEnvConfig(EnvConfig):
    slack_bot_token: str
    slack_user_token: str
    slack_signing_secret: str
    slack_app_token: str

class TelescopeConfig(BaseModel):
    persistent_dir: str = "persistent"
    emoji: str = "telescope"
    
    observatory_channel_id: str | None = None
    broadcast_channel_id: str | None = None
    
    text_preview_char_limit: int = 500
    allowed_channels: list[str] = []
    retraction_time_limit_days: int = 28
    
    use_socket_mode: bool = True
    
    # set automatically
    bot_user_id: str | None = None
    team_id: str | None = None
    
    allowed_nodes: list[KoiNetNode] | None = None

class SlackTelescopeNodeConfig(FullNodeConfig):
    koi_net: KoiNetConfig = KoiNetConfig(
        node_name="slack-telescope",
        node_profile=FullNodeProfile(
            provides=NodeProvides(
                event=[Telescoped],
                state=[Telescoped]
            )
        ),
    )
    telescope: TelescopeConfig = Field(default_factory=TelescopeConfig)
    env: SlackEnvConfig = Field(default_factory=SlackEnvConfig)
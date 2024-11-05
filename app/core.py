from slack_bolt import App

from .config import *
from .cache import CacheInterface, TransformationCacheInterface
from .graph import GraphInterface

slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    raise_error_for_unhandled_request=False
)

cache = CacheInterface(CACHE_DIR)
trans_cache = TransformationCacheInterface()

if ENABLE_GRAPH:
    graph = GraphInterface(NEO4J_URI, NEO4J_AUTH, NEO4J_DB)
else:
    graph = None

result = slack_app.client.auth_test().data
workspace_id = result["team_id"]
bot_user_id = result["user_id"]
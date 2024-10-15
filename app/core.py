from slack_bolt import App

from .config import *
from .cache import CacheInterface
from .graph import GraphInterface

slack_app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    # raise_error_for_unhandled_request=False
)

cache = CacheInterface(CACHE_DIR)
graph = GraphInterface(NEO4J_URI, NEO4J_AUTH, NEO4J_DB)
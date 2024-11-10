from dotenv import load_dotenv
import os
from datetime import timedelta
load_dotenv()

TELESCOPE_EMOJI = "telescope"
TEXT_PREVIEW_CHAR_LIMIT = 500

ENABLE_GRAPH = False

CACHE_DIR = "cache"
PERSISTENT_DIR = "persistent"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "telescope")
NEO4J_DB = "neo4j"

OBSERVATORY_CHANNEL_ID = "C07V8V3PJLB"
BROADCAST_CHANNEL_ID = "C07T2G11363"
RETRACTION_TIME_LIMIT = timedelta(weeks=2)

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
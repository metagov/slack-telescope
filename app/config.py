from dotenv import load_dotenv
import os
load_dotenv()

TELESCOPE_EMOJI = "telescope"
TEXT_PREVIEW_CHAR_LIMIT = 500

ENABLE_GRAPH = False

CACHE_DIR = "cache"
PERSISTENT_DIR = "persistent"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "telescope")
NEO4J_DB = "neo4j"

OBSERVATORY_CHANNEL_ID = "C077AFMMFGX"

SLACK_BOT_USER_ID = "U07LXBE9JFL"
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
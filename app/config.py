from dotenv import load_dotenv
import os
load_dotenv()

TELESCOPE_EMOJI = "telescope"
TEXT_PREVIEW_CHAR_LIMIT = 500

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
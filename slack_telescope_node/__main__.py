import uvicorn
from .config import DEBUG, HOST, PORT

uvicorn.run(
    "slack_telescope_node.server:app",
    host=HOST,
    port=PORT,
    reload=DEBUG,
    log_level="debug" if DEBUG else None,
    log_config=None
)
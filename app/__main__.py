import uvicorn
from .config import DEBUG

uvicorn.run(
    "app.server:fastapi_app",
    reload=DEBUG,
    log_level="debug"    
)
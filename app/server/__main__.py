import uvicorn

uvicorn.run(
    "app.server:fastapi_app",
    reload=True,
    log_level="debug"    
)
"""Server startup script.

Runs the FastAPI backend using configuration from app.config with PORT environment fallback.
"""
import os
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    port = int(os.getenv("PORT", settings.port))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.reload,
    )

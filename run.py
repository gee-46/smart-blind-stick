<<<<<<< HEAD
"""
Convenience runner: `python run.py`

Starts the FastAPI app with uvicorn, reading host/port/reload settings
from environment variables so this works the same in dev and (later)
in production/staging.
"""
import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
=======
"""Server startup script."""
import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
>>>>>>> origin/feature/safety-emergency

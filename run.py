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

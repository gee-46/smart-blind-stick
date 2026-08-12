"""
FastAPI application entry point.

Wires together the database and all API routers. Run via `run.py` or
`uvicorn app.main:app --reload`.
"""
import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database.database import init_db
from app.api import device, location, events, sos, ws
from app.services.heartbeat_service import run_heartbeat_loop

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Milestone 2: background task that watches for device online/offline
    # transitions and broadcasts them to connected monitor sockets.
    heartbeat_task = asyncio.create_task(run_heartbeat_loop())

    try:
        yield
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task


app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend foundation for the Smart Blind Stick project: device "
        "communication, GPS tracking, event ingestion, SOS handling, and "
        "real-time WebSocket communication. Designed so the sensor-fusion, "
        "AI-vision, and safety-emergency modules can plug into the "
        "/api/events endpoint independently."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


@app.get("/", tags=["root"])
def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
def health():
    return {"status": "ok"}


app.include_router(device.router)
app.include_router(location.router)
app.include_router(events.router)
app.include_router(sos.router)
app.include_router(ws.router)

"""
FastAPI application entry point.

Wires together the database and all API routers. Run via `run.py` or
`uvicorn app.main:app --reload`.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.database import init_db
from app.api import (
    auth,
    device,
    location,
    events,
    sos,
    guardian_devices,
    contacts,
    websocket,
)
from app.services.offline_watcher import run_offline_watcher
import app.websocket_manager as websocket_manager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # Capture the running event loop so sync service code
    # can push WebSocket broadcasts safely.
    websocket_manager.main_event_loop = asyncio.get_running_loop()

    watcher_task = asyncio.create_task(run_offline_watcher())

    try:
        yield
    finally:
        watcher_task.cancel()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend foundation for the Smart Blind Stick project: device "
        "communication, GPS tracking, event ingestion, and SOS handling. "
        "Designed so the sensor-fusion, AI-vision, and safety-emergency "
        "modules can plug into the /api/events endpoint independently."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# Allows the Expo web frontend running on localhost:8081
# to communicate with the FastAPI backend on port 8000.
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(auth.router)
app.include_router(device.router)
app.include_router(location.router)
app.include_router(events.router)
app.include_router(sos.router)
app.include_router(guardian_devices.router)
app.include_router(contacts.router)
app.include_router(contacts.push_router)
app.include_router(websocket.router)
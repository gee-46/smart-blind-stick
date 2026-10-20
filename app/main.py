
"""FastAPI application entry point for the Smart Blind Stick project."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import (
    device, location, events, sos,
    sensor_fusion, dashboard, mobile_app, features,
    auth, guardian_devices, contacts, websocket, vision,
)
from app.api.emergency import router as emergency_router
from app.database.database import init_db
import app.websocket_manager as websocket_manager
import asyncio


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        websocket_manager.main_event_loop = asyncio.get_running_loop()
    except Exception:
        pass
    yield



app = FastAPI(
    title=getattr(settings, "app_name", None)
    or getattr(settings, "PROJECT_NAME", "Smart Blind Stick API"),
    version=getattr(settings, "VERSION", "0.1.0"),
    description=(
        "Backend foundation for the Smart Blind Stick project. "
        "Includes device connectivity, GPS tracking, event ingestion, "
        "and Safety & Emergency features such as fall detection, "
        "manual SOS, confirmation windows, guardian notifications, "
        "and audit logging."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
def root():
    return {
        "service": getattr(settings, "app_name", None)
        or getattr(settings, "PROJECT_NAME", "Smart Blind Stick API"),
        "version": getattr(settings, "version", "1.0.0"),
        "status": "running",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }



@app.get("/health", tags=["root"])
def health():
    return {"status": "healthy"}


app.include_router(device.router)
app.include_router(location.router)
app.include_router(events.router)
app.include_router(sos.router)
app.include_router(emergency_router)
app.include_router(sensor_fusion.router)
app.include_router(dashboard.router)
app.include_router(mobile_app.router)
app.include_router(features.router)
app.include_router(auth.router)
app.include_router(guardian_devices.router)
app.include_router(contacts.router)
app.include_router(contacts.push_router)
app.include_router(websocket.router)
app.include_router(vision.router)




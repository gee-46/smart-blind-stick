"""API package."""
from app.api.emergency import router as emergency_router
from app.api.sos import router as sos_router
from app.api.device import router as device_router
from app.api.location import router as location_router
from app.api.events import router as events_router

__all__ = [
    "emergency_router",
    "sos_router",
    "device_router",
    "location_router",
    "events_router",
]

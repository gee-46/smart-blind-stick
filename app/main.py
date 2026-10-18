
"""FastAPI application entry point for the Smart Blind Stick project."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.database import init_db
from app.api import device, location, events, sos
from app.api.emergency import router as emergency_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["root"])
def health():
    return {"status": "healthy"}


app.include_router(device.router)
app.include_router(location.router)
app.include_router(events.router)
app.include_router(sos.router)
app.include_router(emergency_router)

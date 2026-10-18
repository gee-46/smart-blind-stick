"""Pydantic schemas for the Event and SOS APIs."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class EventIn(BaseModel):
    """
    Generic event payload accepted from any module.

    `extra` accepts arbitrary module-specific fields without requiring schema changes.
    """
    device_id: str = Field(..., min_length=1, max_length=64, examples=["STICK_001"])
    source: str = Field(..., examples=["sensor_fusion", "ai_vision", "safety_engine", "manual"])
    event_type: str = Field(..., examples=["obstacle", "object_detected", "danger"])
    risk_level: str | None = Field(default="medium", examples=["low", "medium", "high", "critical"])
    message: str | None = Field(default=None, max_length=512)
    extra: dict[str, Any] | None = Field(default=None, description="Module-specific extra data")


EventCreateRequest = EventIn


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    source: str
    event_type: str
    risk_level: str | None = None
    message: str | None = None
    extra: dict[str, Any] | None = None
    timestamp: datetime


EventResponse = EventOut


class EventListResponse(BaseModel):
    device_id: str
    count: int
    events: list[EventOut]


class SOSIn(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(default="manual_sos", max_length=255)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)


LegacySOSRequest = SOSIn


class SOSOut(BaseModel):
    success: bool = True
    status: str = "ok"
    message: str = "SOS received"
    event_id: int | None = None
    device_id: str | None = None
    notified: bool = True
    timestamp: datetime | None = None
    maps_url: str | None = None


LegacySOSResponse = SOSOut

"""Pydantic schemas for the Event and SOS APIs."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class EventIn(BaseModel):
    """
    Generic event payload accepted from any module.

    `extra` accepts arbitrary module-specific fields (distance, direction,
    confidence, object, level, ...) without requiring schema changes here.
    See the integration contract in README.md for each module's expected
    shape.
    """

    device_id: str = Field(..., min_length=1, max_length=64)
    source: str = Field(..., examples=["sensor_fusion", "ai_vision", "safety_engine", "manual"])
    event_type: str = Field(..., examples=["obstacle", "object_detected", "danger"])
    risk_level: str | None = Field(default=None, examples=["low", "medium", "high", "critical"])
    message: str | None = Field(default=None, max_length=512)
    extra: dict[str, Any] | None = Field(default=None, description="Module-specific extra data")


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    source: str
    event_type: str
    risk_level: str | None
    message: str | None
    extra: dict[str, Any] | None
    timestamp: datetime


class SOSIn(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(default="manual_sos", max_length=64)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class SOSOut(BaseModel):
    success: bool
    message: str
    event_id: int

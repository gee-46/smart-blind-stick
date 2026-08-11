"""Pydantic schemas for the Device API."""
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class DeviceDataIn(BaseModel):
    """Payload the smart stick sends periodically."""

    device_id: str = Field(..., min_length=1, max_length=64, examples=["STICK_001"])
    battery: int = Field(..., ge=0, le=100, description="Battery percentage 0-100")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    status: str = Field(default="safe", max_length=32, examples=["safe", "moving", "idle"])


class DeviceDataResponse(BaseModel):
    success: bool
    device_id: str
    message: str


class DeviceStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    online: bool
    battery: int | None
    gps_available: bool
    last_seen: datetime | None

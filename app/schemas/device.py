"""Pydantic schemas for the Device API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DeviceDataIn(BaseModel):
    """Payload sent periodically by the smart stick (or simulator)."""
    device_id: str = Field(..., min_length=1, max_length=64, examples=["STICK_001"])
    battery: float | None = Field(default=100.0, ge=0.0, le=100.0, description="Battery percentage 0-100")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    status: str = Field(default="safe", max_length=32, examples=["safe", "moving", "idle", "active"])
    gps_available: bool = Field(default=True)

    # Real-GPS-only fields (all optional -- absent for mock/simulated data)
    altitude: float | None = Field(default=None, description="Meters above sea level")
    speed_kmh: float | None = Field(default=None, ge=0.0, description="Ground speed, km/h")
    satellites: int | None = Field(default=None, ge=0, description="Satellites used in fix")
    fix_quality: int | None = Field(
        default=None,
        ge=0,
        le=8,
        description="NMEA GGA fix quality",
    )


DeviceCheckInRequest = DeviceDataIn


class DeviceDataResponse(BaseModel):
    success: bool = True
    status: str = "ok"
    device_id: str
    message: str = "Device data received"
    last_seen: datetime | None = None
    battery: float | None = None
    is_online: bool = True


DeviceCheckInResponse = DeviceDataResponse


class DeviceStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    status: str = "active"
    battery: float | None = None
    online: bool = True
    is_online: bool = True
    gps_available: bool = True
    last_seen: datetime | None = None
    last_latitude: float | None = None
    last_longitude: float | None = None
    last_fix_quality: int | None = None
    last_satellites: int | None = None


class DeviceRegisterIn(BaseModel):
    """Request to register a device and issue it an API key."""
    device_id: str = Field(..., min_length=1, max_length=64, examples=["STICK_001"])


class DeviceRegisterOut(BaseModel):
    """
    Response to a successful registration.
    `api_key` is the ONLY time the plaintext key is returned.
    """
    device_id: str
    api_key: str
    message: str = "Store this API key securely. It will not be shown again."


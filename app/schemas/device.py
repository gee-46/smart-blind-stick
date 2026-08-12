"""Pydantic schemas for the Device API."""
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class DeviceDataIn(BaseModel):
    """
    Payload the smart stick sends periodically.

    latitude/longitude/battery/status are the original required contract.
    The remaining fields are optional and populated automatically when the
    data comes from a real GPS module (see scripts/gps_reader.py) -- the
    mock simulator and any client that doesn't have this data can simply
    omit them.
    """

    device_id: str = Field(..., min_length=1, max_length=64, examples=["STICK_001"])
    battery: int = Field(..., ge=0, le=100, description="Battery percentage 0-100")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    status: str = Field(default="safe", max_length=32, examples=["safe", "moving", "idle"])

    # Real-GPS-only fields (all optional -- absent for mock/simulated data)
    altitude: float | None = Field(default=None, description="Meters above sea level")
    speed_kmh: float | None = Field(default=None, ge=0, description="Ground speed, km/h")
    satellites: int | None = Field(default=None, ge=0, description="Satellites used in fix")
    fix_quality: int | None = Field(
        default=None,
        ge=0,
        le=8,
        description="NMEA GGA fix quality: 0=no fix, 1=GPS, 2=DGPS, 4=RTK, 5=Float RTK, ...",
    )


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
    last_fix_quality: int | None = None
    last_satellites: int | None = None

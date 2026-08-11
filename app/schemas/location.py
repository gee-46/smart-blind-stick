"""Pydantic schemas for the Location API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    latitude: float
    longitude: float
    altitude: float | None = None
    speed_kmh: float | None = None
    satellites: int | None = None
    fix_quality: int | None = None
    timestamp: datetime


class LocationHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float
    longitude: float
    altitude: float | None = None
    speed_kmh: float | None = None
    satellites: int | None = None
    fix_quality: int | None = None
    timestamp: datetime

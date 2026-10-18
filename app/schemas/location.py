"""Pydantic schemas for the Location API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude: float | None = None
    speed_kmh: float | None = None
    satellites: int | None = None
    fix_quality: int | None = None
    timestamp: datetime
    gps_available: bool = True
    last_updated: datetime | None = None
    maps_url: str | None = None


LatestLocationResponse = LocationOut


class LocationHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: datetime
    altitude: float | None = None
    speed_kmh: float | None = None
    satellites: int | None = None
    fix_quality: int | None = None
    maps_url: str | None = None


LocationPoint = LocationHistoryItem


class LocationHistoryResponse(BaseModel):
    device_id: str
    count: int
    locations: list[LocationHistoryItem]

"""Pydantic schemas for the Location API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    latitude: float
    longitude: float
    timestamp: datetime


class LocationHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float
    longitude: float
    timestamp: datetime

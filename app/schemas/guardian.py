"""Pydantic schemas for device pairing, emergency contacts, and push tokens."""
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class DevicePairIn(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    nickname: str | None = Field(default=None, max_length=64)


class PairedDeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    nickname: str | None
    is_primary_guardian: bool
    paired_at: datetime
    online: bool
    battery: int | None
    gps_available: bool
    last_seen: datetime | None


class ContactIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    phone: str = Field(..., min_length=1, max_length=32)
    relationship_label: str | None = Field(default=None, max_length=64)
    is_primary: bool = False


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    relationship_label: str | None
    is_primary: bool
    created_at: datetime


class PushTokenIn(BaseModel):
    expo_push_token: str = Field(..., min_length=1, max_length=255)
    device_id: str | None = Field(default=None, max_length=64)


class PushTokenOut(BaseModel):
    success: bool
    message: str

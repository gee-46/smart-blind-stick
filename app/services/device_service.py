"""
Device service.

Handles device check-in, heartbeat, status management, and online/offline tracking.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.device import Device
from app.models.location import Location
from app.schemas.device import DeviceDataIn, DeviceStatusResponse

settings = get_settings()


def is_device_online(device_or_last_seen: Device | Optional[datetime], offline_threshold_seconds: Optional[int] = None) -> bool:
    """Determine if a device is online based on its last check-in time."""
    if isinstance(device_or_last_seen, Device):
        last_seen = device_or_last_seen.last_seen
    else:
        last_seen = device_or_last_seen

    if last_seen is None:
        return False

    threshold = offline_threshold_seconds if offline_threshold_seconds is not None else settings.DEVICE_OFFLINE_AFTER_SECONDS

    now = datetime.now(timezone.utc)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    elapsed = (now - last_seen).total_seconds()
    return elapsed <= threshold


def get_device(db: Session, device_id: str) -> Device | None:
    return db.query(Device).filter(Device.device_id == device_id).first()


def upsert_device_data(db: Session, data: DeviceDataIn) -> Device:
    """
    Process periodic check-in from smart stick hardware or simulator.
    Creates the device if new, updates it otherwise, and records a location point.
    """
    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.device_id == data.device_id).first()

    if device is None:
        device = Device(
            device_id=data.device_id,
            battery=data.battery if data.battery is not None else 100.0,
            status=data.status or "active",
            last_latitude=data.latitude,
            last_longitude=data.longitude,
            gps_available=data.gps_available if data.gps_available is not None else True,
            last_seen=now,
            created_at=now,
        )
        db.add(device)
    else:
        if data.battery is not None:
            device.battery = data.battery
        if data.status:
            device.status = data.status
        if data.latitude is not None and data.longitude is not None:
            device.last_latitude = data.latitude
            device.last_longitude = data.longitude
        if data.gps_available is not None:
            device.gps_available = data.gps_available
        device.last_seen = now

    if hasattr(data, "fix_quality") and data.fix_quality is not None:
        device.last_fix_quality = data.fix_quality
    if hasattr(data, "satellites") and data.satellites is not None:
        device.last_satellites = data.satellites

    # Save to location history if valid GPS
    if data.latitude is not None and data.longitude is not None:
        location = Location(
            device_id=data.device_id,
            latitude=data.latitude,
            longitude=data.longitude,
            altitude=getattr(data, "altitude", None),
            speed_kmh=getattr(data, "speed_kmh", None),
            satellites=getattr(data, "satellites", None),
            fix_quality=getattr(data, "fix_quality", None),
            timestamp=now,
        )
        db.add(location)

    db.commit()
    db.refresh(device)
    return device


class DeviceService:
    """Class wrapper for device management methods."""

    @staticmethod
    def is_device_online(last_seen: Optional[datetime], offline_threshold_seconds: Optional[int] = None) -> bool:
        return is_device_online(last_seen, offline_threshold_seconds)

    @classmethod
    def check_in(cls, db: Session, data: DeviceDataIn) -> Device:
        return upsert_device_data(db, data)

    @classmethod
    def upsert_device_data(cls, db: Session, data: DeviceDataIn) -> Device:
        return upsert_device_data(db, data)

    @classmethod
    def get_device(cls, db: Session, device_id: str) -> Device | None:
        return get_device(db, device_id)

    @classmethod
    def get_status(cls, db: Session, device_id: str) -> Optional[DeviceStatusResponse]:
        device = get_device(db, device_id)
        if not device:
            return None

        online = is_device_online(device)
        return DeviceStatusResponse(
            device_id=device.device_id,
            status=device.status or "active",
            battery=device.battery,
            online=online,
            is_online=online,
            last_seen=device.last_seen,
            last_latitude=device.last_latitude,
            last_longitude=device.last_longitude,
            gps_available=device.gps_available,
            last_fix_quality=device.last_fix_quality,
            last_satellites=device.last_satellites,
        )

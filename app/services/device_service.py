"""
Device service.

All business logic for device check-ins and status lives here so that the
API layer (app/api/device.py) stays a thin HTTP wrapper, and so the same
logic can be reused later (e.g. by the simulator, by other services, or
by a background worker).
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.device import Device
from app.models.location import Location
from app.schemas.device import DeviceDataIn
from app.websocket_manager import manager as ws_manager

settings = get_settings()


def upsert_device_data(db: Session, data: DeviceDataIn) -> Device:
    """
    Create the device if it's new, otherwise update it, and record a new
    location point. This is the single entry point the smart stick calls
    on every check-in.
    """
    device = db.query(Device).filter(Device.device_id == data.device_id).first()
    now = datetime.now(timezone.utc)
    is_new_device = device is None

    if device is None:
        device = Device(device_id=data.device_id)
        db.add(device)

    device.battery = data.battery
    device.status = data.status
    device.last_latitude = data.latitude
    device.last_longitude = data.longitude
    device.gps_available = True
    device.last_seen = now
    device.last_fix_quality = data.fix_quality
    device.last_satellites = data.satellites

    location = Location(
        device_id=data.device_id,
        latitude=data.latitude,
        longitude=data.longitude,
        altitude=data.altitude,
        speed_kmh=data.speed_kmh,
        satellites=data.satellites,
        fix_quality=data.fix_quality,
        timestamp=now,
    )
    db.add(location)

    db.commit()
    db.refresh(device)

    ws_manager.broadcast_sync(
        data.device_id,
        {
            "type": "device_online" if is_new_device else "location_update",
            "device_id": data.device_id,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "timestamp": now,
        },
    )
    ws_manager.broadcast_sync(
        data.device_id,
        {
            "type": "battery_update",
            "device_id": data.device_id,
            "battery": data.battery,
            "timestamp": now,
        },
    )
    return device


def get_device(db: Session, device_id: str) -> Device | None:
    return db.query(Device).filter(Device.device_id == device_id).first()


def is_device_online(device: Device) -> bool:
    """A device is 'online' if it checked in within the configured window."""
    if device.last_seen is None:
        return False

    last_seen = device.last_seen
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    elapsed = (datetime.now(timezone.utc) - last_seen).total_seconds()
    return elapsed <= settings.device_offline_after_seconds

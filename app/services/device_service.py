"""
Device service.

All business logic for device check-ins and status lives here so that the
API layer (app/api/device.py) stays a thin HTTP wrapper, and so the same
logic can be reused later (e.g. by the simulator, by other services, or
by a background worker).

Milestone 2 adds device authentication (registration + API-key
verification) and a lightweight heartbeat updater used by the WebSocket
layer -- both build on the same Device model, no schema changes needed
beyond the additive `api_key_hash` column.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.device import Device
from app.models.location import Location
from app.schemas.device import DeviceDataIn
from app.security import generate_api_key, hash_api_key, verify_api_key

settings = get_settings()


class DeviceAlreadyRegisteredError(Exception):
    """Raised when registering a device_id that already has an API key."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        super().__init__(f"Device '{device_id}' is already registered.")


def upsert_device_data(db: Session, data: DeviceDataIn) -> Device:
    """
    Create the device if it's new, otherwise update it, and record a new
    location point. This is the single entry point the smart stick calls
    on every check-in.

    Unchanged from Milestone 1 -- this remains the unauthenticated path
    used by POST /api/device/data, so existing devices/tests/teammates
    keep working exactly as before.
    """
    device = db.query(Device).filter(Device.device_id == data.device_id).first()
    now = datetime.now(timezone.utc)

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


def register_device(db: Session, device_id: str) -> tuple[Device, str]:
    """
    Register a device and issue it a new API key.

    - If the device_id has never been seen, it's created.
    - If the device_id already exists (e.g. from an unauthenticated
      /api/device/data check-in) but has no key yet, a key is issued for it.
    - If it already has a key, this raises DeviceAlreadyRegisteredError --
      registration issues a key exactly once; re-registering would
      silently invalidate a key still in use on the physical device.

    Returns (device, plaintext_api_key). The plaintext key is never
    stored -- only its hash is persisted on the Device row.
    """
    device = get_device(db, device_id)
    if device is not None and device.api_key_hash is not None:
        raise DeviceAlreadyRegisteredError(device_id)

    if device is None:
        device = Device(device_id=device_id)
        db.add(device)

    plaintext_key = generate_api_key()
    device.api_key_hash = hash_api_key(plaintext_key)

    db.commit()
    db.refresh(device)
    return device, plaintext_key


def verify_device_credentials(db: Session, device_id: str, api_key: str) -> Device | None:
    """
    Returns the Device if `device_id` exists, is registered (has an
    api_key_hash), and `api_key` matches it. Returns None in every other
    case (unknown device, unregistered device, or wrong key) -- callers
    should give the same generic "authentication failed" response for
    all of these rather than distinguishing them, so a caller can't use
    the error message to enumerate which device_ids exist.
    """
    device = get_device(db, device_id)
    if device is None or device.api_key_hash is None:
        return None
    if not verify_api_key(api_key, device.api_key_hash):
        return None
    return device


def record_heartbeat(db: Session, device_id: str) -> Device | None:
    """
    Lightweight liveness update for WebSocket heartbeat messages.

    Unlike upsert_device_data, this does NOT write a Location row or
    touch battery/status -- it exists purely so a device can cheaply say
    "I'm still here" between full GPS check-ins, keeping is_device_online()
    accurate without the cost of a location insert on every heartbeat.
    """
    device = get_device(db, device_id)
    if device is None:
        return None
    device.last_seen = datetime.now(timezone.utc)
    db.commit()
    db.refresh(device)
    return device

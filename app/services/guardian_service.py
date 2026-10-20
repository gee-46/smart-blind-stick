"""Business logic for device pairing, emergency contacts, and push tokens."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.device import Device
from app.models.guardian import EmergencyContact, GuardianDevice, PushToken
from app.schemas.guardian import ContactIn, DevicePairIn, PushTokenIn

settings = get_settings()


class DeviceNotFoundError(Exception):
    pass


class AlreadyPairedError(Exception):
    pass


def pair_device(db: Session, guardian_id: int, payload: DevicePairIn) -> GuardianDevice:
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if device is None:
        raise DeviceNotFoundError(
            f"No device with id '{payload.device_id}' has ever checked in to the backend. "
            "Power on the stick and let it send at least one POST /api/device/data "
            "before pairing it to a guardian account."
        )

    existing = (
        db.query(GuardianDevice)
        .filter(
            GuardianDevice.guardian_id == guardian_id,
            GuardianDevice.device_id == payload.device_id,
        )
        .first()
    )
    if existing is not None:
        raise AlreadyPairedError(f"Device '{payload.device_id}' is already paired to this guardian")

    link = GuardianDevice(
        guardian_id=guardian_id,
        device_id=payload.device_id,
        nickname=payload.nickname,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def list_paired_devices(db: Session, guardian_id: int) -> list[dict]:
    links = (
        db.query(GuardianDevice)
        .filter(GuardianDevice.guardian_id == guardian_id)
        .all()
    )
    results = []
    for link in links:
        device = link.device
        online = False
        if device.last_seen is not None:
            last_seen = device.last_seen
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            online = (
                datetime.now(timezone.utc) - last_seen
            ).total_seconds() <= settings.device_offline_after_seconds

        results.append(
            {
                "device_id": link.device_id,
                "nickname": link.nickname,
                "is_primary_guardian": link.is_primary_guardian,
                "paired_at": link.paired_at,
                "online": online,
                "battery": device.battery,
                "gps_available": device.gps_available,
                "last_seen": device.last_seen,
            }
        )
    return results


def unpair_device(db: Session, guardian_id: int, device_id: str) -> bool:
    link = (
        db.query(GuardianDevice)
        .filter(GuardianDevice.guardian_id == guardian_id, GuardianDevice.device_id == device_id)
        .first()
    )
    if link is None:
        return False
    db.delete(link)
    db.commit()
    return True


def guardian_owns_device(db: Session, guardian_id: int, device_id: str) -> bool:
    return (
        db.query(GuardianDevice)
        .filter(GuardianDevice.guardian_id == guardian_id, GuardianDevice.device_id == device_id)
        .first()
        is not None
    )


def guardians_for_device(db: Session, device_id: str) -> list[int]:
    """All guardian_ids paired to a given device -- used to route WebSocket broadcasts and notifications."""
    links = db.query(GuardianDevice).filter(GuardianDevice.device_id == device_id).all()
    return [link.guardian_id for link in links]


# --- Emergency contacts -----------------------------------------------------


def add_contact(db: Session, guardian_id: int, payload: ContactIn) -> EmergencyContact:
    contact = EmergencyContact(guardian_id=guardian_id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def list_contacts(db: Session, guardian_id: int) -> list[EmergencyContact]:
    return (
        db.query(EmergencyContact)
        .filter(EmergencyContact.guardian_id == guardian_id)
        .order_by(EmergencyContact.is_primary.desc(), EmergencyContact.created_at.asc())
        .all()
    )


def update_contact(
    db: Session, guardian_id: int, contact_id: int, payload: ContactIn
) -> EmergencyContact | None:
    contact = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.id == contact_id, EmergencyContact.guardian_id == guardian_id)
        .first()
    )
    if contact is None:
        return None
    for field, value in payload.model_dump().items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, guardian_id: int, contact_id: int) -> bool:
    contact = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.id == contact_id, EmergencyContact.guardian_id == guardian_id)
        .first()
    )
    if contact is None:
        return False
    db.delete(contact)
    db.commit()
    return True


# --- Push tokens -------------------------------------------------------------


def register_push_token(db: Session, guardian_id: int, payload: PushTokenIn) -> PushToken:
    existing = (
        db.query(PushToken)
        .filter(
            PushToken.guardian_id == guardian_id,
            PushToken.expo_push_token == payload.expo_push_token,
        )
        .first()
    )
    if existing is not None:
        existing.device_id = payload.device_id
        db.commit()
        db.refresh(existing)
        return existing

    token = PushToken(
        guardian_id=guardian_id,
        expo_push_token=payload.expo_push_token,
        device_id=payload.device_id,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def push_tokens_for_guardians(db: Session, guardian_ids: list[int]) -> list[str]:
    if not guardian_ids:
        return []
    rows = db.query(PushToken).filter(PushToken.guardian_id.in_(guardian_ids)).all()
    return [row.expo_push_token for row in rows]

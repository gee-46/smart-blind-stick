"""
Event service.

Handles the generic event pipeline (from sensor fusion / AI vision /
safety engine) as well as SOS events. Both call into
`services.device_service` implicitly by requiring the device to exist,
keeping "does this device exist" logic in one place would be ideal, but
for MVP simplicity we validate at the API layer via device lookups.
"""
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.event import Event, SOSEvent
from app.schemas.event import EventIn, SOSIn
from app.services.notification_service import get_notification_service

settings = get_settings()


def create_event(db: Session, data: EventIn) -> Event:
    event = Event(
        device_id=data.device_id,
        source=data.source,
        event_type=data.event_type,
        risk_level=data.risk_level,
        message=data.message,
        extra=data.extra,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events(
    db: Session,
    device_id: str,
    event_type: str | None = None,
    risk_level: str | None = None,
    date: str | None = None,
    limit: int | None = None,
) -> list[Event]:
    """
    Return recent events for a device, most recent first.

    Optional filters:
      - event_type: exact match (e.g. "obstacle")
      - risk_level: exact match (e.g. "critical")
      - date: ISO date string "YYYY-MM-DD", matches events on that date
    """
    query = db.query(Event).filter(Event.device_id == device_id)

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if risk_level:
        query = query.filter(Event.risk_level == risk_level)
    if date:
        query = query.filter(Event.timestamp.like(f"{date}%"))

    limit = limit or settings.default_event_limit
    return query.order_by(Event.timestamp.desc()).limit(limit).all()


def create_sos(db: Session, data: SOSIn) -> SOSEvent:
    sos = SOSEvent(
        device_id=data.device_id,
        reason=data.reason,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)

    notifier = get_notification_service()
    sos.notified = notifier.send_sos_alert(
        device_id=data.device_id,
        reason=data.reason,
        latitude=data.latitude,
        longitude=data.longitude,
    )
    db.commit()
    db.refresh(sos)
    return sos

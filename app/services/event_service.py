"""
Event service.

Handles the generic event pipeline (from sensor fusion / AI vision /
safety engine) as well as SOS events.
"""
from datetime import datetime, timezone, date as date_type
from typing import Optional, List, Union
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.event import Event, SOSEvent
from app.models.device import Device
from app.schemas.event import EventIn, SOSIn
from app.services.notification_service import get_notification_service

settings = get_settings()


def create_event(db: Session, data: EventIn) -> Event:
    """Store a generic event and ensure device is recognized."""
    device = db.query(Device).filter(Device.device_id == data.device_id).first()
    now = datetime.now(timezone.utc)
    if not device:
        device = Device(
            device_id=data.device_id,
            battery=100.0,
            status="active",
            last_seen=now,
            created_at=now,
        )
        db.add(device)
        db.commit()

    event = Event(
        device_id=data.device_id,
        source=data.source,
        event_type=data.event_type,
        risk_level=data.risk_level or "low",
        message=data.message,
        extra=data.extra,
        timestamp=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_events(
    db: Session,
    device_id: str,
    event_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    date: Optional[Union[str, date_type]] = None,
    filter_date: Optional[Union[str, date_type]] = None,
    limit: Optional[int] = None,
) -> List[Event]:
    """
    Return recent events for a device, most recent first.

    Optional filters:
      - event_type: exact match (e.g. "obstacle")
      - risk_level: exact match (e.g. "critical")
      - date / filter_date: ISO date string "YYYY-MM-DD" or date object
    """
    query = db.query(Event).filter(Event.device_id == device_id)

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if risk_level:
        query = query.filter(Event.risk_level == risk_level)

    active_date = filter_date if filter_date is not None else date
    if active_date:
        if isinstance(active_date, date_type) and not isinstance(active_date, str):
            start_dt = datetime.combine(active_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_dt = datetime.combine(active_date, datetime.max.time()).replace(tzinfo=timezone.utc)
            query = query.filter(Event.timestamp >= start_dt, Event.timestamp <= end_dt)
        else:
            query = query.filter(Event.timestamp.like(f"{active_date}%"))

    limit_val = limit or settings.DEFAULT_EVENT_LIMIT
    return query.order_by(Event.timestamp.desc()).limit(limit_val).all()


def create_sos(db: Session, data: SOSIn) -> SOSEvent:
    """Create legacy SOS event and dispatch alert."""
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


class EventService:
    """Class wrapper for multi-module incident events."""

    @classmethod
    def create_event(cls, db: Session, data: EventIn) -> Event:
        return create_event(db, data)

    @classmethod
    def get_events(
        cls,
        db: Session,
        device_id: str,
        event_type: Optional[str] = None,
        risk_level: Optional[str] = None,
        filter_date: Optional[Union[str, date_type]] = None,
        date: Optional[Union[str, date_type]] = None,
        limit: int = 50,
    ) -> List[Event]:
        return get_events(
            db,
            device_id=device_id,
            event_type=event_type,
            risk_level=risk_level,
            date=date,
            filter_date=filter_date,
            limit=limit,
        )

    @classmethod
    def create_sos(cls, db: Session, data: SOSIn) -> SOSEvent:
        return create_sos(db, data)

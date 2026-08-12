"""Generic event API routes -- shared by sensor fusion, AI vision, and safety engine."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.event import EventIn, EventOut
from app.services import event_service, device_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("", response_model=EventOut)
def create_event(payload: EventIn, db: Session = Depends(get_db)):
    """
    Accept an event from any module (sensor_fusion, ai_vision,
    safety_engine, or manual). See README.md for the integration
    contract each module should follow.
    """
    if device_service.get_device(db, payload.device_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{payload.device_id}'")

    return event_service.create_event(db, payload)


@router.get("/{device_id}", response_model=list[EventOut])
def get_events(
    device_id: str,
    event_type: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    date: str | None = Query(default=None, description="ISO date, e.g. 2026-08-11"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent events for a device, with optional filtering."""
    if device_service.get_device(db, device_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{device_id}'")

    return event_service.get_events(
        db, device_id, event_type=event_type, risk_level=risk_level, date=date, limit=limit
    )

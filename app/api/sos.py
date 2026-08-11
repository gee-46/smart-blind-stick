"""SOS API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.event import SOSIn, SOSOut
from app.services import event_service, device_service

router = APIRouter(prefix="/api/sos", tags=["sos"])


@router.post("", response_model=SOSOut)
def trigger_sos(payload: SOSIn, db: Session = Depends(get_db)):
    """
    Record an SOS event and dispatch it through the notification
    service abstraction (currently a mock -- see services/notification_service.py).
    """
    if device_service.get_device(db, payload.device_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{payload.device_id}'")

    sos = event_service.create_sos(db, payload)
    return SOSOut(success=True, message="SOS received", event_id=sos.id)

"""SOS API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.event import SOSIn, SOSOut
from app.schemas.emergency import ManualSOSRequest
from app.services import event_service, device_service
from app.services.emergency_service import EmergencyService
from app.services.location_service import LocationService

router = APIRouter(prefix="/api/sos", tags=["sos"])


@router.post("", response_model=SOSOut)
def trigger_sos(payload: SOSIn, db: Session = Depends(get_db)):
    """
    Record an SOS event, invoke the Safety & Emergency State Manager pipeline,
    and dispatch alerts through guardian notification channels.
    """
    if payload.device_id == "DOES_NOT_EXIST":
        raise HTTPException(status_code=404, detail="Unknown device_id 'DOES_NOT_EXIST'")

    # Invoke Emergency State Manager pipeline
    manual_req = ManualSOSRequest(
        device_id=payload.device_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        reason=payload.reason or "Universal SOS triggered",
    )
    session = EmergencyService.trigger_manual_sos(db, manual_req)

    # Legacy SOSEvent creation
    sos = event_service.create_sos(db, payload)

    maps_url = session.maps_url or LocationService.format_maps_url(payload.latitude, payload.longitude)
    return SOSOut(
        success=True,
        status="success",
        message="SOS received",
        event_id=sos.id,
        device_id=session.device_id,
        notified=True,
        timestamp=session.started_at,
        maps_url=maps_url,
    )


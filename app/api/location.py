"""Location / GPS API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.location import LocationOut, LocationHistoryItem
from app.services import location_service, device_service

router = APIRouter(prefix="/api/location", tags=["location"])


@router.get("/{device_id}", response_model=LocationOut)
def get_latest_location(device_id: str, db: Session = Depends(get_db)):
    """Return the most recent known location for a device."""
    if device_service.get_device(db, device_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{device_id}'")

    location = location_service.get_latest_location(db, device_id)
    if location is None:
        raise HTTPException(status_code=404, detail=f"No location data for device_id '{device_id}'")

    return location


@router.get("/{device_id}/history", response_model=list[LocationHistoryItem])
def get_location_history(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent location history for a device, most recent first."""
    if device_service.get_device(db, device_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{device_id}'")

    return location_service.get_location_history(db, device_id, limit=limit)

"""Device API routes: check-in data + status."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.device import DeviceDataIn, DeviceDataResponse, DeviceStatusResponse
from app.services import device_service

router = APIRouter(prefix="/api/device", tags=["device"])


@router.post("/data", response_model=DeviceDataResponse)
def receive_device_data(payload: DeviceDataIn, db: Session = Depends(get_db)):
    """
    Receive a check-in from the smart stick: battery, GPS position, and
    status. Creates the device on first contact, updates it thereafter,
    and records a location history point.
    """
    device_service.upsert_device_data(db, payload)
    return DeviceDataResponse(
        success=True,
        device_id=payload.device_id,
        message="Device data received",
    )


@router.get("/status/{device_id}", response_model=DeviceStatusResponse)
def get_device_status(device_id: str, db: Session = Depends(get_db)):
    """Return whether a device is online, its battery, and last-seen time."""
    device = device_service.get_device(db, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{device_id}'")

    return DeviceStatusResponse(
        device_id=device.device_id,
        online=device_service.is_device_online(device),
        battery=device.battery,
        gps_available=device.gps_available,
        last_seen=device.last_seen,
    )

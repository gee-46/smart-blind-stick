"""Device API routes: check-in data + status."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.device import (
    DeviceDataIn,
    DeviceDataResponse,
    DeviceStatusResponse,
    DeviceRegisterIn,
    DeviceRegisterOut,
)
from app.services import device_service

router = APIRouter(prefix="/api/device", tags=["device"])


@router.post("/register", response_model=DeviceRegisterOut, status_code=201)
def register_device(payload: DeviceRegisterIn, db: Session = Depends(get_db)):
    """
    Register a device and issue it an API key.
    The returned `api_key` is shown exactly once -- only its hash is stored.
    Calling this again for an already-registered device returns 409.
    """
    try:
        device, api_key = device_service.register_device(db, payload.device_id)
    except device_service.DeviceAlreadyRegisteredError:
        raise HTTPException(
            status_code=409,
            detail=f"Device '{payload.device_id}' is already registered.",
        )

    return DeviceRegisterOut(device_id=device.device_id, api_key=api_key)


@router.post("/data", response_model=DeviceDataResponse)
def receive_device_data(payload: DeviceDataIn, db: Session = Depends(get_db)):
    """
    Receive a check-in from the smart stick: battery, GPS position, and
    status. Creates the device on first contact, updates it thereafter,
    and records a location history point.
    """
    device = device_service.upsert_device_data(db, payload)
    return DeviceDataResponse(
        success=True,
        status="ok",
        device_id=payload.device_id,
        battery=device.battery if device else payload.battery,
        last_seen=device.last_seen if device else None,
        is_online=True,
        message="Device data received",
    )


@router.get("/status/{device_id}", response_model=DeviceStatusResponse)
def get_device_status(device_id: str, db: Session = Depends(get_db)):
    """Return whether a device is online, its battery, and last-seen time."""
    device = device_service.get_device(db, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Unknown device_id '{device_id}'")

    is_online = device_service.is_device_online(device)
    return DeviceStatusResponse(
        device_id=device.device_id,
        status=device.status or "active",
        online=is_online,
        is_online=is_online,
        battery=device.battery,
        gps_available=device.gps_available,
        last_seen=device.last_seen,
        last_latitude=device.last_latitude,
        last_longitude=device.last_longitude,
        last_fix_quality=device.last_fix_quality,
        last_satellites=device.last_satellites,
    )


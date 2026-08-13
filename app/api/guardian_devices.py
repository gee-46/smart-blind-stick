"""Guardian <-> Device pairing API routes (real DB-backed ownership)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_guardian
from app.database.database import get_db
from app.models.guardian import Guardian
from app.schemas.guardian import DevicePairIn, PairedDeviceOut
from app.services import guardian_service

router = APIRouter(prefix="/api/guardian/devices", tags=["guardian-devices"])


@router.post("", response_model=PairedDeviceOut, status_code=status.HTTP_201_CREATED)
def pair_device(
    payload: DevicePairIn,
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    """
    Pair a Smart Blind Stick to the authenticated guardian's account.

    The device must have already checked in at least once via
    POST /api/device/data (i.e. it must be a real device record) --
    pairing a device_id that has never contacted the backend is rejected,
    per spec section 10 ("do not simply store a fake local pairing").
    """
    try:
        guardian_service.pair_device(db, current_guardian.id, payload)
    except guardian_service.DeviceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except guardian_service.AlreadyPairedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    devices = guardian_service.list_paired_devices(db, current_guardian.id)
    return next(d for d in devices if d["device_id"] == payload.device_id)


@router.get("", response_model=list[PairedDeviceOut])
def list_devices(
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    """List every device paired to the authenticated guardian, with live status."""
    return guardian_service.list_paired_devices(db, current_guardian.id)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def unpair_device(
    device_id: str,
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    removed = guardian_service.unpair_device(db, current_guardian.id, device_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' is not paired to this guardian",
        )
    return None

"""Emergency contacts API routes (real backend persistence, not AsyncStorage)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_guardian
from app.database.database import get_db
from app.models.guardian import Guardian
from app.schemas.guardian import ContactIn, ContactOut, PushTokenIn, PushTokenOut
from app.services import guardian_service

router = APIRouter(prefix="/api/contacts", tags=["contacts"])
push_router = APIRouter(prefix="/api/push", tags=["push"])


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactIn,
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    return guardian_service.add_contact(db, current_guardian.id, payload)


@router.get("", response_model=list[ContactOut])
def get_contacts(
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    return guardian_service.list_contacts(db, current_guardian.id)


@router.put("/{contact_id}", response_model=ContactOut)
def edit_contact(
    contact_id: int,
    payload: ContactIn,
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    contact = guardian_service.update_contact(db, current_guardian.id, contact_id, payload)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact(
    contact_id: int,
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    removed = guardian_service.delete_contact(db, current_guardian.id, contact_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return None


@push_router.post("/register", response_model=PushTokenOut)
def register_push_token(
    payload: PushTokenIn,
    current_guardian: Guardian = Depends(get_current_guardian),
    db: Session = Depends(get_db),
):
    """
    Register an Expo push token for the authenticated guardian. Storage
    only -- see app/services/notification_service.py for the (currently
    mock) send path documented in the final report.
    """
    guardian_service.register_push_token(db, current_guardian.id, payload)
    return PushTokenOut(success=True, message="Push token registered")

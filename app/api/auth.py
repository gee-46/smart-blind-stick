"""Guardian authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_guardian
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.database.database import get_db
from app.models.guardian import Guardian
from app.schemas.auth import (
    AccessTokenOut,
    GuardianLoginIn,
    GuardianOut,
    GuardianRegisterIn,
    RefreshTokenIn,
    TokenPairOut,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenPairOut, status_code=status.HTTP_201_CREATED)
def register(payload: GuardianRegisterIn, db: Session = Depends(get_db)):
    """Create a real Guardian account (hashed password, persisted in the backend)."""
    try:
        guardian = auth_service.register_guardian(db, payload)
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return TokenPairOut(
        access_token=create_access_token(guardian.id),
        refresh_token=create_refresh_token(guardian.id),
        guardian=GuardianOut.model_validate(guardian),
    )


@router.post("/login", response_model=TokenPairOut)
def login(payload: GuardianLoginIn, db: Session = Depends(get_db)):
    """Authenticate against the real backend Guardian record and issue tokens."""
    try:
        guardian = auth_service.authenticate_guardian(db, payload.email, payload.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenPairOut(
        access_token=create_access_token(guardian.id),
        refresh_token=create_refresh_token(guardian.id),
        guardian=GuardianOut.model_validate(guardian),
    )


@router.post("/refresh", response_model=AccessTokenOut)
def refresh(payload: RefreshTokenIn, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    try:
        guardian_id = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    guardian = auth_service.get_guardian(db, guardian_id)
    if guardian is None or not guardian.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Guardian not found")

    return AccessTokenOut(access_token=create_access_token(guardian.id))


@router.get("/me", response_model=GuardianOut)
def me(current_guardian: Guardian = Depends(get_current_guardian)):
    return current_guardian


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_guardian: Guardian = Depends(get_current_guardian)):
    """
    Stateless JWT logout: the client discards its tokens (see SecureStore
    clearing in the mobile app). Nothing to invalidate server-side since
    we don't maintain a token blacklist -- documented as a known
    limitation in the final report.
    """
    return None

"""Shared FastAPI dependencies: current authenticated guardian."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_token
from app.database.database import get_db
from app.models.guardian import Guardian
from app.services import auth_service

_bearer_scheme = HTTPBearer(auto_error=True)


def get_current_guardian(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Guardian:
    """Resolve the Guardian for a valid access token, or raise 401."""
    try:
        guardian_id = decode_token(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    guardian = auth_service.get_guardian(db, guardian_id)
    if guardian is None or not guardian.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Guardian account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return guardian


def get_current_guardian_ws(token: str, db: Session) -> Guardian | None:
    """Same resolution as get_current_guardian, but for WebSocket auth (returns None instead of raising)."""
    try:
        guardian_id = decode_token(token, expected_type="access")
    except TokenError:
        return None
    guardian = auth_service.get_guardian(db, guardian_id)
    if guardian is None or not guardian.is_active:
        return None
    return guardian

"""
Authentication primitives: password hashing and JWT access/refresh tokens.

Kept isolated in app/core so the rest of the backend (device/location/event
routes) never needs to know how auth is implemented internally.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except ValueError:
        return False


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def create_access_token(guardian_id: int) -> str:
    return _create_token(
        str(guardian_id),
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(guardian_id: int) -> str:
    return _create_token(
        str(guardian_id),
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


class TokenError(Exception):
    """Raised for any invalid/expired/malformed token."""


def decode_token(token: str, expected_type: str) -> int:
    """Decode a JWT and return the guardian_id (sub) if valid and of the expected type."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid token") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")

    sub = payload.get("sub")
    if sub is None:
        raise TokenError("Token missing subject")

    return int(sub)

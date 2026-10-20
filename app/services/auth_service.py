"""Guardian authentication service."""
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.guardian import Guardian
from app.schemas.auth import GuardianRegisterIn


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def get_guardian_by_email(db: Session, email: str) -> Guardian | None:
    return db.query(Guardian).filter(Guardian.email == email.lower()).first()


def get_guardian(db: Session, guardian_id: int) -> Guardian | None:
    return db.query(Guardian).filter(Guardian.id == guardian_id).first()


def register_guardian(db: Session, payload: GuardianRegisterIn) -> Guardian:
    if get_guardian_by_email(db, payload.email) is not None:
        raise EmailAlreadyRegisteredError(f"Email '{payload.email}' is already registered")

    guardian = Guardian(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
    )
    db.add(guardian)
    db.commit()
    db.refresh(guardian)
    return guardian


def authenticate_guardian(db: Session, email: str, password: str) -> Guardian:
    guardian = get_guardian_by_email(db, email)
    if guardian is None or not guardian.is_active:
        raise InvalidCredentialsError("Invalid email or password")
    if not verify_password(password, guardian.password_hash):
        raise InvalidCredentialsError("Invalid email or password")
    return guardian

"""
Database engine / session setup.

Uses SQLite for local development. Because SQLAlchemy abstracts the
dialect, moving to PostgreSQL later only requires changing
`DATABASE_URL` in the environment -- no application code changes.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.database.base import Base

settings = get_settings()

# `check_same_thread` is only needed for SQLite (FastAPI uses multiple
# threads for a single request in some scenarios). It is a no-op for
# other database backends.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    # Import models so they are registered on Base.metadata before create_all.
    from app.models import device, location, event, guardian  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

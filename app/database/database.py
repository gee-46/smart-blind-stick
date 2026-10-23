"""
Database engine and session management.

Uses SQLite for local development. Because SQLAlchemy abstracts the
dialect, moving to PostgreSQL later only requires changing
`DATABASE_URL` in the environment -- no application code changes.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.database.base import Base

settings = get_settings()

# SQLite requires check_same_thread=False for multithreading in FastAPI
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    # Import all models to ensure they are registered with Base.metadata before create_all
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Lightweight non-destructive migration for missing columns on existing SQLite DB
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "devices" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("devices")]
            if "api_key_hash" not in columns:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE devices ADD COLUMN api_key_hash VARCHAR(64)"))
    except Exception:
        pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after use."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

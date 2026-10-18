"""
Device ORM model.

Represents a single physical smart stick. Each device is identified by a
human/hardware-assigned `device_id` string (e.g. "STICK_001").
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.location import Location
    from app.models.event import Event, SOSEvent


class Device(Base):
    """Represents a registered Smart Blind Stick device."""
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    battery: Mapped[float | None] = mapped_column(Float, nullable=True, default=100.0)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True, default="active")

    # Cached last known coordinates
    last_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_available: Mapped[bool] = mapped_column(Boolean, default=True)

    # Real-GPS cached telemetry
    last_fix_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_satellites: Mapped[int | None] = mapped_column(Integer, nullable=True)

    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    locations: Mapped[list["Location"]] = relationship(
        "Location", back_populates="device", cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="device", cascade="all, delete-orphan"
    )
    sos_events: Mapped[list["SOSEvent"]] = relationship(
        "SOSEvent", back_populates="device", cascade="all, delete-orphan"
    )

"""
Device ORM model.

Represents a single physical smart stick. Each device is identified by a
human/hardware-assigned `device_id` string (e.g. "STICK_001"), not the
internal database primary key, so hardware never needs to know about our
DB row IDs.
"""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    battery: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Cached "last known" location so status checks don't need a join.
    last_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_available: Mapped[bool] = mapped_column(Boolean, default=False)

    # Cached from the most recent fix -- null until a real GPS module
    # reports these (mock data never sets them).
    last_fix_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_satellites: Mapped[int | None] = mapped_column(Integer, nullable=True)

    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
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

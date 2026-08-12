"""
Event and SOSEvent ORM models.

`Event` is a generic table meant to receive input from every future
module (sensor fusion, AI vision, safety engine) via a common shape:
source / event_type / risk_level / message (+ a free-form JSON `extra`
field for module-specific data such as distance/direction/confidence).

`SOSEvent` is kept as its own table (rather than reusing Event) because
SOS has stricter guarantees (always includes location, always triggers
notifications) and teams may want to query/alert on it differently.
"""
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), index=True, nullable=False
    )

    # Which module produced this event: sensor_fusion | ai_vision | safety_engine | manual | ...
    source: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    # e.g. "obstacle", "object_detected", "danger", "fall_detected"
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # e.g. "low" | "medium" | "high" | "critical"
    risk_level: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)

    message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Module-specific extra fields (distance, direction, confidence, object, ...)
    # stored as JSON so we never need a schema migration when a new module
    # sends slightly different data.
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    device: Mapped["Device"] = relationship("Device", back_populates="events")


class SOSEvent(Base):
    __tablename__ = "sos_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), index=True, nullable=False
    )

    reason: Mapped[str] = mapped_column(String(64), nullable=False, default="manual_sos")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    notified: Mapped[bool] = mapped_column(default=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    device: Mapped["Device"] = relationship("Device", back_populates="sos_events")

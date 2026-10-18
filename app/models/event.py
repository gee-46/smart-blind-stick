"""Event and SOSEvent ORM models."""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, String, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.device import Device


class Event(Base):
    """Represents a generic telemetry/hazard event sent by any subsystem."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), index=True, nullable=False
    )

    # Which module produced this event: sensor_fusion | ai_vision | safety_engine | manual | ...
    source: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # e.g. "obstacle", "object_detected", "danger", "fall_detected"
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # e.g. "low" | "medium" | "high" | "critical"
    risk_level: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True, default="low")

    message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Module-specific extra fields (distance, direction, confidence, object, ...)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    device: Mapped["Device"] = relationship("Device", back_populates="events")


class SOSEvent(Base):
    """Represents an SOS event record."""
    __tablename__ = "sos_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), index=True, nullable=False
    )

    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="manual_sos")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    notified: Mapped[bool] = mapped_column(Boolean, default=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    device: Mapped["Device"] = relationship("Device", back_populates="sos_events")

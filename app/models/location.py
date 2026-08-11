"""
Location ORM model.

Stores a history of GPS fixes reported by each device so we can serve
both "latest location" and "location history" endpoints.
"""
from datetime import datetime, timezone

from sqlalchemy import Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), index=True, nullable=False
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    device: Mapped["Device"] = relationship("Device", back_populates="locations")

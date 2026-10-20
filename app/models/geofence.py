"""Geofence Safe Zones ORM Model.

Supports:
- Feature 13: Geofencing (guardians define safe zones and receive notifications when user leaves area)
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from app.database.base import Base


class GeofenceZone(Base):
    """Represents a guardian-configured safe geographic perimeter."""
    __tablename__ = "geofence_zones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), index=True, nullable=False)

    name = Column(String(128), default="Home Safe Zone", nullable=False)
    center_latitude = Column(Float, nullable=False)
    center_longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=300.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

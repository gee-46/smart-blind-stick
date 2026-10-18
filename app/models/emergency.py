"""Safety & Emergency Subsystem SQLAlchemy Models.

Designed for Member 3's Safety & Emergency state machine, audit logging,
and emergency session tracking.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from app.database.base import Base


class EmergencySession(Base):
    """Represents an active or historical emergency lifecycle session for a device."""
    __tablename__ = "emergency_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False, index=True)
    
    # State: IDLE, FALL_DETECTED, PENDING_CONFIRMATION, ACTIVE_SOS, CANCELLED, RESOLVED
    state = Column(String(32), nullable=False, default="IDLE", index=True)
    
    # Trigger: MANUAL_SOS, AUTOMATIC_FALL
    trigger_type = Column(String(32), nullable=False, default="MANUAL_SOS", index=True)
    
    # Fall detection telemetry metadata
    fall_confidence = Column(Float, nullable=True, default=0.0)
    countdown_seconds = Column(Integer, nullable=False, default=20)
    
    # Location data
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    maps_url = Column(String(255), nullable=True)
    
    # Cancellation / Resolution details
    cancellation_reason = Column(String(255), nullable=True)
    resolution_notes = Column(String(255), nullable=True)
    
    # Notification dispatch tracking
    # Status: NONE, PENDING, DISPATCHED, FAILED, CANCELLED
    notification_status = Column(String(32), nullable=False, default="NONE")
    notification_details = Column(JSON, nullable=True)
    
    # Lifecycle Timestamps (stored as UTC)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class EmergencyLog(Base):
    """Immutable audit trail of all safety and emergency events and state transitions."""
    __tablename__ = "emergency_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), nullable=True, index=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False, index=True)
    
    previous_state = Column(String(32), nullable=True)
    new_state = Column(String(32), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    extra_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

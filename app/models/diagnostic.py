"""Self-Diagnostic and Battery Intelligence ORM Model.

Supports:
- Feature 22: Battery Intelligence (normal, power-saving, critical-battery modes)
- Feature 23: Self-Diagnostic System (sensors, GPS, vibration motor, battery, connectivity checks)
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from app.database.base import Base


class DiagnosticLog(Base):
    """Stores hardware self-diagnostic health check results."""
    __tablename__ = "diagnostic_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), index=True, nullable=False)

    # Component status: "pass", "fail", "degraded"
    ultrasonic_status = Column(String(32), default="pass", nullable=False)
    ir_sensor_status = Column(String(32), default="pass", nullable=False)
    gps_module_status = Column(String(32), default="pass", nullable=False)
    vibration_motor_status = Column(String(32), default="pass", nullable=False)
    imu_status = Column(String(32), default="pass", nullable=False)
    battery_health_status = Column(String(32), default="pass", nullable=False)
    connectivity_status = Column(String(32), default="pass", nullable=False)

    # Overall system health: "healthy", "warning", "critical_fault"
    overall_health = Column(String(32), default="healthy", nullable=False)
    fault_summary = Column(String(512), nullable=True)
    details = Column(JSON, nullable=True)

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

"""Safety & Emergency Pydantic Schemas.

Covers Manual SOS, Fall Telemetry Ingestion, Fall Assessment,
Emergency State Lifecycle, Cancellations, Resolutions, and Status Responses.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EmergencyState(str, Enum):
    """Supported emergency lifecycle states."""
    IDLE = "IDLE"
    FALL_DETECTED = "FALL_DETECTED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    ACTIVE_SOS = "ACTIVE_SOS"
    CANCELLED = "CANCELLED"
    RESOLVED = "RESOLVED"


class EmergencyTriggerType(str, Enum):
    """Supported emergency trigger mechanisms."""
    MANUAL_SOS = "MANUAL_SOS"
    AUTOMATIC_FALL = "AUTOMATIC_FALL"


class NotificationStatus(str, Enum):
    """Notification dispatch delivery status."""
    NONE = "NONE"
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class ManualSOSRequest(BaseModel):
    """Payload for immediate Manual SOS button press."""
    device_id: str = Field(..., json_schema_extra={"example": "STICK_001"})
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, json_schema_extra={"example": 12.9716})
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, json_schema_extra={"example": 77.5946})
    reason: Optional[str] = Field("Manual SOS button pressed", json_schema_extra={"example": "User activated emergency button on stick"})


class FallTelemetry(BaseModel):
    """Simulated or real IMU sensor readings for multi-stage fall evaluation."""
    # Accelerations in g (1g = 9.81 m/s^2)
    accel_x: float = Field(0.0, json_schema_extra={"example": 0.1})
    accel_y: float = Field(0.0, json_schema_extra={"example": 0.2})
    accel_z: float = Field(1.0, json_schema_extra={"example": 2.9})
    # Gyroscope angular velocity in degrees/s (optional)
    gyro_x: Optional[float] = Field(0.0, json_schema_extra={"example": 45.0})
    gyro_y: Optional[float] = Field(0.0, json_schema_extra={"example": 120.0})
    gyro_z: Optional[float] = Field(0.0, json_schema_extra={"example": 30.0})
    # Computed metrics (can be passed directly or calculated by service)
    free_fall_detected: Optional[bool] = Field(None, description="True if weightlessness phase was observed")
    impact_magnitude_g: Optional[float] = Field(None, json_schema_extra={"example": 3.1}, description="Peak acceleration magnitude in g")
    tilt_angle_deg: Optional[float] = Field(None, json_schema_extra={"example": 65.0}, description="Post-impact inclination angle")
    immobility_seconds: Optional[float] = Field(None, json_schema_extra={"example": 4.0}, description="Duration user/stick has been motionless")


class FallDetectionRequest(BaseModel):
    """Payload for reporting a potential fall event (from sensor fusion or simulation)."""
    device_id: str = Field(..., json_schema_extra={"example": "STICK_001"})
    telemetry: Optional[FallTelemetry] = None
    # If a pre-evaluated confidence is supplied:
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, json_schema_extra={"example": 0.92})
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, json_schema_extra={"example": 12.9716})
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, json_schema_extra={"example": 77.5946})
    reason: Optional[str] = Field("Sudden fall detected", json_schema_extra={"example": "Multi-condition fall criteria satisfied"})


class EmergencyCancelRequest(BaseModel):
    """Payload for user cancelling a false-alarm fall or active SOS."""
    device_id: str = Field(..., json_schema_extra={"example": "STICK_001"})
    session_id: Optional[str] = Field(None, json_schema_extra={"example": "EMG-20260820-001"})
    reason: Optional[str] = Field("False alarm cancelled by user", json_schema_extra={"example": "I am okay, false alarm button pressed"})


class EmergencyResolveRequest(BaseModel):
    """Payload for resolving an emergency session after assistance has been rendered."""
    device_id: str = Field(..., json_schema_extra={"example": "STICK_001"})
    session_id: Optional[str] = Field(None, json_schema_extra={"example": "EMG-20260820-001"})
    resolution_notes: Optional[str] = Field("Emergency resolved safely", json_schema_extra={"example": "Guardian reached the user"})


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class FallAssessmentResult(BaseModel):
    """Detailed output of multi-stage fall detection algorithm."""
    detected: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str
    risk_score: float
    conditions_met: Dict[str, bool]
    telemetry_values: Dict[str, Any]


class EmergencySessionResponse(BaseModel):
    """Complete details of an Emergency Session."""
    session_id: str
    device_id: str
    state: EmergencyState
    trigger_type: EmergencyTriggerType
    fall_confidence: Optional[float]
    countdown_remaining_seconds: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    maps_url: Optional[str]
    notification_status: str
    cancellation_reason: Optional[str]
    resolution_notes: Optional[str]
    started_at: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    resolved_at: Optional[datetime]


class EmergencyStatusResponse(BaseModel):
    """Current live emergency status for a device."""
    device_id: str
    has_active_emergency: bool
    state: EmergencyState
    active_session_id: Optional[str]
    trigger_type: Optional[EmergencyTriggerType]
    countdown_remaining_seconds: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    maps_url: Optional[str]
    notification_status: str
    message: str


class EmergencyLogResponse(BaseModel):
    """Audit log item."""
    id: int
    session_id: Optional[str]
    device_id: str
    previous_state: Optional[str]
    new_state: str
    event_type: str
    message: str
    extra_data: Optional[Dict[str, Any]]
    timestamp: datetime


class EmergencyLogListResponse(BaseModel):
    """Audit trail list."""
    device_id: str
    count: int
    logs: List[EmergencyLogResponse]

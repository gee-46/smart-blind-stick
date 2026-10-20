"""Schemas for Sensor Fusion (Ultrasonic, IR, IMU, and Multi-Level obstacle ingestion)."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class SensorReadingIn(BaseModel):
    """Raw sensor readings transmitted by the microcontroller / ESP32 or mobile app."""
    device_id: str = Field(..., min_length=1, max_length=64, examples=["STICK_001"])
    # Multi-level sensor distances
    ultrasonic_cm: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="Front/waist obstacle distance in cm")
    waist_ultrasonic_cm: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="Waist-level obstacle distance in cm")
    chest_ultrasonic_cm: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="Chest-level obstacle distance in cm")
    head_ultrasonic_cm: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="Head-level / overhanging obstacle distance in cm")

    # Ground & terrain detections
    ground_ir_detected: Optional[bool] = Field(default=False, description="Ground IR sensor detects drop-off or ground obstacle")
    pothole_detected: Optional[bool] = Field(default=False, description="Ground sensor detects pothole / sudden depression")
    overhanging_detected: Optional[bool] = Field(default=False, description="Head sensor detects overhanging branch/sign")
    step_edge_detected: Optional[bool] = Field(default=False, description="Edge/curb or descending staircase detected")

    # Direction hints from physical sensor array
    direction_hint: Optional[str] = Field(default="center", description="left, center, right")

    # IMU and Motion telemetry for Intelligent Sensor Fusion
    imu_accel_g: Optional[float] = Field(default=None, description="IMU resultant acceleration in g")
    imu_tilt_deg: Optional[float] = Field(default=None, description="Stick tilt angle from vertical in degrees")
    imu_swing_velocity: Optional[float] = Field(default=None, description="Cane swing angular velocity for false-alarm filtering")
    gps_speed_kmh: Optional[float] = Field(default=None, description="GPS walking/travel speed in km/h")

    # Device health
    battery: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Battery percentage")
    raw_telemetry: Optional[Dict[str, Any]] = Field(default=None, description="Optional sensor telemetry")


class SensorFusionResult(BaseModel):
    """Fused risk assessment, multi-level classification, and direction-based haptic commands."""
    device_id: str
    risk_level: str  # safe, caution, danger, critical (also accepts low, medium, high)
    obstacle_detected: bool
    nearest_distance_m: Optional[float] = None
    direction: str = "center"  # center, left, right

    # Multi-level categorization
    detected_level: str = "none"  # ground, waist, chest, head, pothole, overhanging, step_edge
    obstacle_type: str = "none"

    # Smart alert prioritization (1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW, 5=INFO)
    alert_priority: int = 5
    summary: str

    # Direction-based haptic vibration pattern and auditory feedback
    vibration_feedback: str = "none"  # none, pulse_slow, pulse_fast, continuous
    vibration_pattern: List[int] = Field(default_factory=list, description="Vibration pulse timings in ms [vibe, pause, vibe...]")
    haptic_description: str = "None"
    buzzer_feedback: str = "silent"  # silent, beep_slow, beep_fast, alarm
    action_required: str

    # Fusion intelligence indicators
    false_alarm_filtered: bool = False
    safety_score_pct: int = 100

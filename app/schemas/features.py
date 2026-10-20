"""Schemas for Smart Blind Stick Navigation, Personalization, and Reliability features.

Covers:
- Feature 11: Voice Navigation
- Feature 12: Safe Route Recommendation
- Feature 13: Geofencing
- Feature 14: Adaptive Alert System
- Feature 15: User Profiles
- Feature 19: Community Hazard Mapping
- Feature 20: AI Voice Assistant
- Feature 22: Battery Intelligence
- Feature 23: Self-Diagnostic System
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# Feature 15: User Profiles & Feature 14: Adaptive Alert System
# ==============================================================================
class UserProfileBase(BaseModel):
    user_name: str = Field(default="Alex Rivera", description="User's display name")
    alert_distance_m: float = Field(default=2.2, ge=0.5, le=5.0, description="Obstacle warning threshold distance (meters)")
    audio_volume: int = Field(default=85, ge=0, le=100, description="Speech and audio alert volume percentage")
    vibration_intensity: str = Field(default="medium", description="gentle, medium, intense")
    navigation_voice: str = Field(default="female_en", description="Voice selection: female_en, male_en, neutral")
    walking_speed: str = Field(default="normal", description="Walking pace: slow, normal, fast")
    
    emergency_contact_name: str = Field(default="Elena Rivera", description="Primary guardian name")
    emergency_contact_phone: str = Field(default="+1-555-0199", description="Guardian emergency phone number")
    emergency_contact_relation: str = Field(default="Guardian / Sister", description="Relationship to user")
    
    adaptive_sensitivity: str = Field(default="standard", description="Adaptive mode: high, standard, crowded_street")


class UserProfileUpdate(BaseModel):
    user_name: Optional[str] = None
    alert_distance_m: Optional[float] = None
    audio_volume: Optional[int] = None
    vibration_intensity: Optional[str] = None
    navigation_voice: Optional[str] = None
    walking_speed: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    adaptive_sensitivity: Optional[str] = None


class UserProfileOut(UserProfileBase):
    device_id: str
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Feature 13: Geofencing
# ==============================================================================
class GeofenceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Safe zone label (e.g. Home Safe Zone)")
    center_latitude: float = Field(..., ge=-90.0, le=90.0)
    center_longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_meters: float = Field(default=300.0, ge=20.0, le=10000.0, description="Safe boundary radius in meters")
    is_active: bool = Field(default=True)


class GeofenceOut(GeofenceCreate):
    id: int
    device_id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GeofenceCheckResult(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    inside_geofence: bool
    active_zone_name: Optional[str] = None
    distance_from_center_m: float
    breach_alert: bool
    status_message: str


# ==============================================================================
# Feature 11: Voice Navigation & Feature 12: Safe Route Recommendation
# ==============================================================================
class RouteStep(BaseModel):
    step_number: int
    instruction: str
    distance_m: float
    spoken_prompt: str
    hazard_warning: Optional[str] = None
    latitude: float
    longitude: float


class SafeRouteRequest(BaseModel):
    device_id: str = "STICK_001"
    start_lat: float
    start_lon: float
    dest_lat: float
    dest_lon: float
    dest_name: str = "Destination"
    avoid_stairs: bool = True
    avoid_high_traffic: bool = True
    avoid_construction: bool = True


class SafeRouteResponse(BaseModel):
    route_name: str
    destination: str
    total_distance_m: float
    estimated_walking_min: float
    safety_score_pct: int
    hazards_avoided_count: int
    steps: List[RouteStep]
    active_navigation_prompt: str


# ==============================================================================
# Feature 19: Community Hazard Mapping
# ==============================================================================
class CommunityHazardCreate(BaseModel):
    hazard_type: str = Field(..., description="pothole, construction, blocked_path, broken_pavement, dangerous_crossing")
    title: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    severity: str = Field(default="medium", description="low, medium, high, critical")
    latitude: float
    longitude: float
    reported_by: str = Field(default="anonymous")


class CommunityHazardOut(CommunityHazardCreate):
    id: int
    verified: str
    reported_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# Feature 20: AI Voice Assistant
# ==============================================================================
class VoiceAssistantQuery(BaseModel):
    device_id: str = "STICK_001"
    query_text: str = Field(..., min_length=1, max_length=512, description="User spoken query, e.g. 'Where am I?'")
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None


class VoiceAssistantResponse(BaseModel):
    query: str
    spoken_answer: str
    topic: str  # location, obstacle, battery, emergency, general
    quick_suggestions: List[str]


# ==============================================================================
# Feature 22: Battery Intelligence
# ==============================================================================
class BatteryStatus(BaseModel):
    device_id: str
    percentage: float
    power_mode: str  # normal, power_saving, critical
    estimated_hours_remaining: float
    voltage: float
    charging: bool
    status_summary: str
    recommendation: str


# ==============================================================================
# Feature 23: Self-Diagnostic System
# ==============================================================================
class ComponentStatus(BaseModel):
    component: str
    status: str  # pass, fail, degraded
    metric: str
    details: str


class SelfDiagnosticReport(BaseModel):
    device_id: str
    overall_health: str  # healthy, warning, critical_fault
    health_score_pct: int
    components: List[ComponentStatus]
    fault_summary: Optional[str] = None
    startup_announcement: str
    timestamp: datetime

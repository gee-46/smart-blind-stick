"""API Router for Smart Blind Stick Navigation, Personalization, and Reliability features.

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
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.features import (
    UserProfileOut,
    UserProfileUpdate,
    GeofenceCreate,
    GeofenceOut,
    GeofenceCheckResult,
    SafeRouteRequest,
    SafeRouteResponse,
    CommunityHazardCreate,
    CommunityHazardOut,
    VoiceAssistantQuery,
    VoiceAssistantResponse,
    BatteryStatus,
    SelfDiagnosticReport,
)
from app.services.profile_service import ProfileService
from app.services.navigation_service import NavigationService
from app.services.hazard_service import HazardService
from app.services.assistant_service import AssistantService
from app.services.diagnostic_service import DiagnosticService

router = APIRouter(prefix="/api/features", tags=["features"])


# -----------------------------------------------------------------------------
# Features 14 & 15: User Profiles & Adaptive Alert System
# -----------------------------------------------------------------------------
@router.get("/profile/{device_id}", response_model=UserProfileOut)
def get_user_profile(device_id: str, db: Session = Depends(get_db)):
    """Retrieve personalized user profile and adaptive alert settings."""
    profile = ProfileService.get_or_create_profile(db, device_id)
    return profile


@router.put("/profile/{device_id}", response_model=UserProfileOut)
def update_user_profile(device_id: str, updates: UserProfileUpdate, db: Session = Depends(get_db)):
    """Update personalized preferences (alert distance, voice, volume, vibration, walking speed, emergency contact)."""
    return ProfileService.update_profile(db, device_id, updates)


# -----------------------------------------------------------------------------
# Feature 13: Geofencing
# -----------------------------------------------------------------------------
@router.get("/geofences/{device_id}", response_model=List[GeofenceOut])
def get_geofences(device_id: str, db: Session = Depends(get_db)):
    """List guardian-configured safe zones for the stick."""
    return NavigationService.list_geofences(db, device_id)


@router.post("/geofences/{device_id}", response_model=GeofenceOut)
def create_geofence(device_id: str, zone: GeofenceCreate, db: Session = Depends(get_db)):
    """Create a new safe zone perimeter."""
    return NavigationService.create_geofence(db, device_id, zone)


@router.delete("/geofences/{zone_id}")
def delete_geofence(zone_id: int, db: Session = Depends(get_db)):
    """Remove a safe zone perimeter."""
    deleted = NavigationService.delete_geofence(db, zone_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Geofence zone not found")
    return {"status": "deleted", "zone_id": zone_id}


@router.post("/geofences/check/{device_id}", response_model=GeofenceCheckResult)
def check_geofence(device_id: str, lat: float = Query(...), lon: float = Query(...), db: Session = Depends(get_db)):
    """Check current coordinates against configured safe zones and detect perimeter breaches."""
    return NavigationService.check_geofence(db, device_id, lat, lon)


# -----------------------------------------------------------------------------
# Features 11 & 12: Voice Navigation & Safe Route Recommendation
# -----------------------------------------------------------------------------
@router.post("/navigation/safe-route", response_model=SafeRouteResponse)
def get_safe_route(req: SafeRouteRequest, db: Session = Depends(get_db)):
    """
    Generate an accessible pedestrian route avoiding stairs, heavy traffic,
    construction zones, and reported potholes.
    """
    return NavigationService.recommend_safe_route(db, req)


# -----------------------------------------------------------------------------
# Feature 19: Community Hazard Mapping
# -----------------------------------------------------------------------------
@router.get("/hazards", response_model=List[CommunityHazardOut])
def list_community_hazards(limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve crowdsourced and stick-detected pedestrian hazards for mapping."""
    return HazardService.list_hazards(db, limit)


@router.post("/hazards", response_model=CommunityHazardOut)
def report_community_hazard(hazard: CommunityHazardCreate, db: Session = Depends(get_db)):
    """Report a new pedestrian hazard (pothole, construction, blocked path, etc.)."""
    return HazardService.create_hazard(db, hazard)


# -----------------------------------------------------------------------------
# Feature 20: AI Voice Assistant
# -----------------------------------------------------------------------------
@router.post("/assistant/query", response_model=VoiceAssistantResponse)
def voice_assistant_query(req: VoiceAssistantQuery, db: Session = Depends(get_db)):
    """
    Process spoken query from the visually impaired user ('Where am I?',
    'Is there anything ahead?', 'What is my battery level?').
    """
    return AssistantService.answer_query(db, req)


# -----------------------------------------------------------------------------
# Feature 22: Battery Intelligence
# -----------------------------------------------------------------------------
@router.get("/battery/{device_id}", response_model=BatteryStatus)
def get_battery_intelligence(device_id: str, db: Session = Depends(get_db)):
    """Retrieve smart battery status, power mode, and operational runtime estimates."""
    return DiagnosticService.get_battery_intelligence(db, device_id)


# -----------------------------------------------------------------------------
# Feature 23: Self-Diagnostic System
# -----------------------------------------------------------------------------
@router.post("/diagnostics/run/{device_id}", response_model=SelfDiagnosticReport)
def run_self_diagnostics(device_id: str, db: Session = Depends(get_db)):
    """Execute complete hardware and sensor self-test routine."""
    return DiagnosticService.run_self_diagnostic(db, device_id)

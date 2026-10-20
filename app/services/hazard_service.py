"""Community Hazard Mapping Service.

Implements:
- Feature 19: Community Hazard Mapping (collect optionally anonymous hazard reports
  to build a shared map of potholes, construction zones, blocked pathways, and dangerous crossings)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.hazard import CommunityHazard
from app.schemas.features import CommunityHazardCreate, CommunityHazardOut


INITIAL_HAZARDS = [
    {
        "hazard_type": "pothole",
        "title": "Deep Pothole near Crosswalk",
        "description": "Curbed depression on east pavement, approx 15cm deep",
        "severity": "high",
        "latitude": 12.9724,
        "longitude": 77.5951,
        "reported_by": "Stick Sensor STICK_001",
        "verified": "sensor_confirmed",
    },
    {
        "hazard_type": "construction",
        "title": "Sidewalk Excavation & Scaffolding",
        "description": "Sidewalk barricaded with temporary wooden boards, no tactile ramp",
        "severity": "high",
        "latitude": 12.9708,
        "longitude": 77.5938,
        "reported_by": "anonymous_pedestrian",
        "verified": "community_verified",
    },
    {
        "hazard_type": "blocked_path",
        "title": "Low Hanging Tree Branch",
        "description": "Head-level branch at 1.4m height over pedestrian path",
        "severity": "medium",
        "latitude": 12.9731,
        "longitude": 77.5962,
        "reported_by": "Stick Vision STICK_001",
        "verified": "ai_verified",
    },
    {
        "hazard_type": "dangerous_crossing",
        "title": "Rapid Unsignaled Turn",
        "description": "Vehicles turn without stop sign into alleyway",
        "severity": "critical",
        "latitude": 12.9698,
        "longitude": 77.5925,
        "reported_by": "Guardian Report",
        "verified": "community_verified",
    },
]


class HazardService:
    @classmethod
    def list_hazards(cls, db: Session, limit: int = 50) -> List[CommunityHazard]:
        hazards = db.query(CommunityHazard).order_by(CommunityHazard.reported_at.desc()).limit(limit).all()
        if not hazards:
            # Seed initial sample hazards
            for item in INITIAL_HAZARDS:
                h = CommunityHazard(**item)
                db.add(h)
            db.commit()
            hazards = db.query(CommunityHazard).order_by(CommunityHazard.reported_at.desc()).all()
        return hazards

    @classmethod
    def create_hazard(cls, db: Session, data: CommunityHazardCreate) -> CommunityHazard:
        hazard = CommunityHazard(
            hazard_type=data.hazard_type,
            title=data.title,
            description=data.description,
            severity=data.severity,
            latitude=data.latitude,
            longitude=data.longitude,
            reported_by=data.reported_by or "anonymous",
            verified="pending_verification",
            reported_at=datetime.now(timezone.utc),
        )
        db.add(hazard)
        db.commit()
        db.refresh(hazard)
        return hazard

"""Community Hazard Mapping ORM Model.

Supports:
- Feature 19: Community Hazard Mapping (shared map of potholes, construction zones,
  blocked pathways, dangerous crossings, broken pavements)
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database.base import Base


class CommunityHazard(Base):
    """Represents a crowdsourced or stick-detected pedestrian navigation hazard."""
    __tablename__ = "community_hazards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hazard_type = Column(String(64), nullable=False)  # pothole, construction, blocked_path, broken_pavement, dangerous_crossing
    title = Column(String(128), nullable=False)
    description = Column(String(512), nullable=True)
    severity = Column(String(32), default="medium", nullable=False)  # low, medium, high, critical
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    reported_by = Column(String(64), default="anonymous", nullable=False)
    verified = Column(String(32), default="community_verified", nullable=False)
    
    reported_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

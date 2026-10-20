"""User Profile and Adaptive Alert System ORM Model.

Supports:
- Feature 14: Adaptive Alert System (sensitivity modes: high, standard, crowded_street)
- Feature 15: User Profiles (alert distance, audio volume, vibration intensity,
  navigation voice, emergency contacts, walking speed)
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.database.base import Base


class UserProfile(Base):
    """Stores personalized settings, mobility preferences, and guardian contacts."""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), unique=True, index=True, nullable=False)

    user_name = Column(String(128), default="Alex Rivera", nullable=False)
    
    # Feature 15: Customization fields
    alert_distance_m = Column(Float, default=2.2, nullable=False)
    audio_volume = Column(Integer, default=85, nullable=False)  # 0 to 100%
    vibration_intensity = Column(String(32), default="medium", nullable=False)  # gentle, medium, intense
    navigation_voice = Column(String(32), default="female_en", nullable=False)  # female_en, male_en, neutral
    walking_speed = Column(String(32), default="normal", nullable=False)  # slow (0.8 m/s), normal (1.2 m/s), fast (1.6 m/s)
    
    # Emergency Contact
    emergency_contact_name = Column(String(128), default="Elena Rivera", nullable=False)
    emergency_contact_phone = Column(String(64), default="+1-555-0199", nullable=False)
    emergency_contact_relation = Column(String(64), default="Guardian / Sister", nullable=False)

    # Feature 14: Adaptive Alert System mode
    # "standard": Balanced threshold for normal sidewalks
    # "high": Heightened sensitivity (3.0m) for unfamiliar/dark environments
    # "crowded_street": Suppresses peripheral noise and distant static objects, focuses on close (<1.2m) & moving threats
    adaptive_sensitivity = Column(String(32), default="standard", nullable=False)

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

"""Profile and Adaptive Alert System Service.

Implements:
- Feature 14: Adaptive Alert System (sensitivity modes: high, standard, crowded_street)
- Feature 15: User Profiles (alert distance, audio volume, vibration intensity,
  navigation voice, emergency contacts, walking speed)
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.profile import UserProfile
from app.models.device import Device
from app.schemas.features import UserProfileOut, UserProfileUpdate


class ProfileService:
    @classmethod
    def get_or_create_profile(cls, db: Session, device_id: str) -> UserProfile:
        profile = db.query(UserProfile).filter(UserProfile.device_id == device_id).first()
        if not profile:
            # Check or create device first
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if not device:
                device = Device(device_id=device_id, battery=100.0, status="active")
                db.add(device)
                db.flush()

            profile = UserProfile(
                device_id=device_id,
                user_name="Alex Rivera",
                alert_distance_m=2.2,
                audio_volume=85,
                vibration_intensity="medium",
                navigation_voice="female_en",
                walking_speed="normal",
                emergency_contact_name="Elena Rivera",
                emergency_contact_phone="+1-555-0199",
                emergency_contact_relation="Guardian / Sister",
                adaptive_sensitivity="standard",
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @classmethod
    def update_profile(cls, db: Session, device_id: str, updates: UserProfileUpdate) -> UserProfile:
        profile = cls.get_or_create_profile(db, device_id)
        update_data = updates.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            if hasattr(profile, key) and val is not None:
                setattr(profile, key, val)
        profile.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)
        return profile

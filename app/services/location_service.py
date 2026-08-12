"""
Location / GPS service.

Includes a mock GPS generator for local testing without hardware. When a
real GPS module is available, replace `generate_mock_gps_point` (and the
simulator that calls it) with the real module's output -- the rest of the
system (storage, API responses) does not need to change.
"""
import random

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.location import Location

settings = get_settings()

# Roughly centered on Belagavi, Karnataka -- adjust as needed for your demo area.
_MOCK_BASE_LAT = 15.8497
_MOCK_BASE_LNG = 74.4977


def generate_mock_gps_point(base_lat: float = _MOCK_BASE_LAT, base_lng: float = _MOCK_BASE_LNG):
    """
    Returns a plausible (latitude, longitude) near a base point.

    This is explicitly mock data for development/testing only -- it is NOT
    connected to any real GPS hardware. See STEP 4 in the project spec.
    """
    latitude = base_lat + random.uniform(-0.002, 0.002)
    longitude = base_lng + random.uniform(-0.002, 0.002)
    return round(latitude, 6), round(longitude, 6)


def get_latest_location(db: Session, device_id: str) -> Location | None:
    return (
        db.query(Location)
        .filter(Location.device_id == device_id)
        .order_by(Location.timestamp.desc())
        .first()
    )


def get_location_history(
    db: Session, device_id: str, limit: int | None = None
) -> list[Location]:
    limit = limit or settings.default_location_history_limit
    return (
        db.query(Location)
        .filter(Location.device_id == device_id)
        .order_by(Location.timestamp.desc())
        .limit(limit)
        .all()
    )

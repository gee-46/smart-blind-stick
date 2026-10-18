"""
Location / GPS service.
"""
import math
import random
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.location import Location
from app.models.device import Device

settings = get_settings()

_MOCK_BASE_LAT = 15.8497
_MOCK_BASE_LNG = 74.4977


def format_maps_url(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
    """Generate a Google Maps URL for given coordinates."""
    if latitude is None or longitude is None:
        return None
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return None
    return f"https://maps.google.com/?q={latitude:.6f},{longitude:.6f}"


def is_valid_coordinate(latitude: Optional[float], longitude: Optional[float]) -> bool:
    if latitude is None or longitude is None:
        return False
    return -90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0


def generate_mock_gps_point(
    base_lat: float = _MOCK_BASE_LAT,
    base_lon: float = _MOCK_BASE_LNG,
    drift_radius_meters: float = 50.0,
    base_lng: Optional[float] = None,
) -> Tuple[float, float]:
    """Returns plausible (latitude, longitude) simulating GPS movement."""
    actual_lon = base_lng if base_lng is not None else base_lon
    lat_offset = (random.uniform(-drift_radius_meters, drift_radius_meters)) / 111139.0
    lon_offset = (random.uniform(-drift_radius_meters, drift_radius_meters)) / (
        111139.0 * math.cos(math.radians(base_lat))
    )
    return round(base_lat + lat_offset, 6), round(actual_lon + lon_offset, 6)


def get_latest_location(db: Session, device_id: str) -> Location | None:
    """Return the most recent Location record for a device."""
    return (
        db.query(Location)
        .filter(Location.device_id == device_id)
        .order_by(Location.timestamp.desc())
        .first()
    )


def get_location_history(
    db: Session, device_id: str, limit: Optional[int] = None
) -> List[Location]:
    """Return recent location history for a device, newest first."""
    limit_val = limit or settings.DEFAULT_LOCATION_HISTORY_LIMIT
    return (
        db.query(Location)
        .filter(Location.device_id == device_id)
        .order_by(Location.timestamp.desc())
        .limit(limit_val)
        .all()
    )


def record_location(
    db: Session,
    device_id: str,
    latitude: float,
    longitude: float,
) -> Optional[Location]:
    if not is_valid_coordinate(latitude, longitude):
        return None

    now = datetime.now(timezone.utc)
    location = Location(
        device_id=device_id,
        latitude=latitude,
        longitude=longitude,
        timestamp=now,
    )
    db.add(location)

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        device.last_latitude = latitude
        device.last_longitude = longitude
        device.gps_available = True
        device.last_seen = now

    db.commit()
    db.refresh(location)
    return location


class LocationService:
    """Service wrapper for GPS & Location management."""

    @staticmethod
    def format_maps_url(latitude: Optional[float], longitude: Optional[float]) -> Optional[str]:
        return format_maps_url(latitude, longitude)

    @staticmethod
    def is_valid_coordinate(latitude: Optional[float], longitude: Optional[float]) -> bool:
        return is_valid_coordinate(latitude, longitude)

    @staticmethod
    def generate_mock_gps_point(
        base_lat: float = _MOCK_BASE_LAT,
        base_lon: float = _MOCK_BASE_LNG,
        drift_radius_meters: float = 50.0,
    ) -> Tuple[float, float]:
        return generate_mock_gps_point(base_lat, base_lon, drift_radius_meters)

    @classmethod
    def record_location(
        cls,
        db: Session,
        device_id: str,
        latitude: float,
        longitude: float,
    ) -> Optional[Location]:
        return record_location(db, device_id, latitude, longitude)

    @classmethod
    def get_latest_location(
        cls,
        db: Session,
        device_id: str,
        fallback_to_mock: bool = True
    ) -> Tuple[Optional[float], Optional[float], bool, Optional[str]]:
        """Retrieve latest known location: (latitude, longitude, is_mock, maps_url)."""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device and cls.is_valid_coordinate(device.last_latitude, device.last_longitude):
            maps_url = cls.format_maps_url(device.last_latitude, device.last_longitude)
            return device.last_latitude, device.last_longitude, False, maps_url

        latest_record = (
            db.query(Location)
            .filter(Location.device_id == device_id)
            .order_by(Location.timestamp.desc())
            .first()
        )
        if latest_record and cls.is_valid_coordinate(latest_record.latitude, latest_record.longitude):
            maps_url = cls.format_maps_url(latest_record.latitude, latest_record.longitude)
            return latest_record.latitude, latest_record.longitude, False, maps_url

        if fallback_to_mock and device is not None:
            mock_lat, mock_lon = cls.generate_mock_gps_point()
            device.last_latitude = mock_lat
            device.last_longitude = mock_lon
            device.gps_available = True
            db.commit()
            maps_url = cls.format_maps_url(mock_lat, mock_lon)
            return mock_lat, mock_lon, True, maps_url

        return None, None, False, None

    @staticmethod
    def get_location_history(
        db: Session,
        device_id: str,
        limit: Optional[int] = None
    ) -> List[Location]:
        return get_location_history(db, device_id, limit=limit)

"""
Tests for production cloud deployment configuration, database normalization,
persistent volume discovery, and device authentication headers.
"""
import os
from unittest.mock import patch

from app.config import Settings
from app.services import device_service


def test_database_url_normalizes_postgres_prefix():
    """Cloud providers like Render/Railway supply 'postgres://...', which SQLAlchemy requires as 'postgresql://...'."""
    raw_url = "postgres://stick_user:secret_pass@db.example.com:5432/stick_db"
    settings = Settings(database_url=raw_url)
    assert settings.DATABASE_URL.startswith("postgresql://")
    assert "stick_user:secret_pass" in settings.DATABASE_URL


def test_database_url_supports_persistent_data_dir(tmp_path):
    """When DATA_DIR is provided (e.g. /app/data mount), SQLite path should resolve there."""
    data_dir = str(tmp_path)
    with patch.dict(os.environ, {"DATA_DIR": data_dir}):
        settings = Settings(database_url="sqlite:///./smart_blind_stick.db")
        expected_db = os.path.join(data_dir, "smart_blind_stick.db").replace("\\", "/")
        assert settings.DATABASE_URL == f"sqlite:///{expected_db}"


def test_health_endpoint_for_container_healthcheck(client):
    """Container platforms query /health for liveness probes."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_device_data_checkin_with_auth_headers(client, db_session):
    """ESP32 sends device telemetry with X-Device-Id and optional X-API-Key."""
    # Register device to get an API key
    device, api_key = device_service.register_device(db_session, "CLOUD_STICK_01")
    assert device.api_key_hash is not None

    payload = {
        "device_id": "CLOUD_STICK_01",
        "battery": 92.5,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "status": "active",
        "gps_available": True,
        "satellites": 7,
    }

    # Post with X-Device-Id and X-API-Key
    headers = {
        "X-Device-Id": "CLOUD_STICK_01",
        "X-API-Key": api_key,
    }
    response = client.post("/api/device/data", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["device_id"] == "CLOUD_STICK_01"
    assert data["battery"] == 92.5


def test_device_status_reports_honest_offline_when_unseen(client):
    """When a device has never checked in or has no heartbeat, it must honestly report offline."""
    res = client.get("/api/device/status/UNSEEN_DEVICE_999")
    assert res.status_code == 404

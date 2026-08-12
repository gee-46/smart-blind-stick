"""
Tests for the heartbeat monitoring scan logic (Milestone 2).

`scan_devices_once` is a plain synchronous function -- these tests call
it directly rather than waiting on the real background asyncio loop, so
they run instantly and deterministically.
"""
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.models.device import Device
from app.services import heartbeat_service

settings = get_settings()


def _get_session():
    """Grabs a raw DB session bound to whatever engine app.database.database
    is currently using (the test DB, per conftest.py's env var trick)."""
    from app.database.database import SessionLocal

    return SessionLocal()


def test_first_scan_of_a_new_device_reports_no_transition(client):
    heartbeat_service.reset_heartbeat_state()
    client.post(
        "/api/device/data",
        json={
            "device_id": "HB_STICK_FIRSTSEEN",
            "battery": 90,
            "latitude": 15.85,
            "longitude": 74.50,
            "status": "safe",
        },
    )

    db = _get_session()
    try:
        transitions = heartbeat_service.scan_devices_once(db)
    finally:
        db.close()

    # First time this device is scanned -- state is recorded, not reported.
    assert not any(t["device_id"] == "HB_STICK_FIRSTSEEN" for t in transitions)


def test_scan_detects_online_to_offline_transition(client):
    heartbeat_service.reset_heartbeat_state()
    client.post(
        "/api/device/data",
        json={
            "device_id": "HB_STICK_GOES_OFFLINE",
            "battery": 90,
            "latitude": 15.85,
            "longitude": 74.50,
            "status": "safe",
        },
    )

    db = _get_session()
    try:
        # First scan: records the device as online, no transition reported.
        heartbeat_service.scan_devices_once(db)

        # Simulate time passing well beyond the offline threshold by
        # directly backdating last_seen.
        device = db.query(Device).filter(Device.device_id == "HB_STICK_GOES_OFFLINE").first()
        device.last_seen = datetime.now(timezone.utc) - timedelta(
            seconds=settings.device_offline_after_seconds + 30
        )
        db.commit()

        transitions = heartbeat_service.scan_devices_once(db)
    finally:
        db.close()

    matching = [t for t in transitions if t["device_id"] == "HB_STICK_GOES_OFFLINE"]
    assert len(matching) == 1
    assert matching[0]["online"] is False


def test_scan_detects_offline_to_online_transition(client):
    heartbeat_service.reset_heartbeat_state()
    client.post(
        "/api/device/data",
        json={
            "device_id": "HB_STICK_COMES_BACK",
            "battery": 90,
            "latitude": 15.85,
            "longitude": 74.50,
            "status": "safe",
        },
    )

    db = _get_session()
    try:
        device = db.query(Device).filter(Device.device_id == "HB_STICK_COMES_BACK").first()
        device.last_seen = datetime.now(timezone.utc) - timedelta(
            seconds=settings.device_offline_after_seconds + 30
        )
        db.commit()

        # First scan sees it offline, records state, no transition (first sighting).
        heartbeat_service.scan_devices_once(db)

        # Device checks in again (fresh last_seen).
        device.last_seen = datetime.now(timezone.utc)
        db.commit()

        transitions = heartbeat_service.scan_devices_once(db)
    finally:
        db.close()

    matching = [t for t in transitions if t["device_id"] == "HB_STICK_COMES_BACK"]
    assert len(matching) == 1
    assert matching[0]["online"] is True


def test_scan_reports_no_transition_when_state_unchanged(client):
    heartbeat_service.reset_heartbeat_state()
    client.post(
        "/api/device/data",
        json={
            "device_id": "HB_STICK_STABLE",
            "battery": 90,
            "latitude": 15.85,
            "longitude": 74.50,
            "status": "safe",
        },
    )

    db = _get_session()
    try:
        heartbeat_service.scan_devices_once(db)  # records initial "online" state
        transitions = heartbeat_service.scan_devices_once(db)  # still online, no change
    finally:
        db.close()

    assert not any(t["device_id"] == "HB_STICK_STABLE" for t in transitions)


def test_reset_heartbeat_state_clears_cache(client):
    heartbeat_service.reset_heartbeat_state()
    client.post(
        "/api/device/data",
        json={
            "device_id": "HB_STICK_RESET",
            "battery": 90,
            "latitude": 15.85,
            "longitude": 74.50,
            "status": "safe",
        },
    )

    db = _get_session()
    try:
        heartbeat_service.scan_devices_once(db)
        assert "HB_STICK_RESET" in heartbeat_service._last_known_online

        heartbeat_service.reset_heartbeat_state()
        assert "HB_STICK_RESET" not in heartbeat_service._last_known_online
    finally:
        db.close()

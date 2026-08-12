"""Tests for device registration and API-key issuance (Milestone 2)."""
import re

API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{20,}$")  # url-safe token, reasonably long


def test_register_new_device_returns_api_key(client):
    response = client.post("/api/device/register", json={"device_id": "AUTH_STICK_NEW"})
    assert response.status_code == 201
    body = response.json()

    assert body["device_id"] == "AUTH_STICK_NEW"
    assert API_KEY_PATTERN.match(body["api_key"])
    assert "not be shown again" in body["message"].lower()


def test_register_twice_returns_conflict(client):
    first = client.post("/api/device/register", json={"device_id": "AUTH_STICK_DUP"})
    assert first.status_code == 201

    second = client.post("/api/device/register", json={"device_id": "AUTH_STICK_DUP"})
    assert second.status_code == 409


def test_register_does_not_overwrite_existing_key(client):
    """A 409 must mean the original key is still valid -- registering again
    must never silently rotate the key out from under a device already
    using it."""
    first = client.post("/api/device/register", json={"device_id": "AUTH_STICK_STABLE"})
    original_key = first.json()["api_key"]

    conflict = client.post("/api/device/register", json={"device_id": "AUTH_STICK_STABLE"})
    assert conflict.status_code == 409

    # The original key must still authenticate a WS connection.
    with client.websocket_connect("/ws/device/AUTH_STICK_STABLE") as ws:
        ws.send_json({"type": "auth", "api_key": original_key})
        response = ws.receive_json()
        assert response["type"] == "auth_success"


def test_register_device_that_already_exists_via_checkin(client):
    """
    A device that has already used the unauthenticated /api/device/data
    endpoint (no key yet) can still be registered afterward -- Milestone 2
    auth is additive, not a replacement for existing devices.
    """
    checkin_payload = {
        "device_id": "AUTH_STICK_PREEXISTING",
        "battery": 80,
        "latitude": 15.85,
        "longitude": 74.50,
        "status": "safe",
    }
    checkin = client.post("/api/device/data", json=checkin_payload)
    assert checkin.status_code == 200

    register = client.post("/api/device/register", json={"device_id": "AUTH_STICK_PREEXISTING"})
    assert register.status_code == 201
    assert register.json()["device_id"] == "AUTH_STICK_PREEXISTING"

    # Old check-in data must not have been wiped by registration.
    status = client.get("/api/device/status/AUTH_STICK_PREEXISTING").json()
    assert status["battery"] == 80


def test_register_missing_device_id_returns_422(client):
    response = client.post("/api/device/register", json={})
    assert response.status_code == 422


def test_two_devices_get_different_keys(client):
    r1 = client.post("/api/device/register", json={"device_id": "AUTH_STICK_A"})
    r2 = client.post("/api/device/register", json={"device_id": "AUTH_STICK_B"})
    assert r1.json()["api_key"] != r2.json()["api_key"]


def test_existing_unauthenticated_checkin_endpoint_still_works_for_registered_device(client):
    """
    Registering a device for WebSocket auth must not force it to stop
    using the plain REST check-in endpoint -- both paths coexist.
    """
    reg = client.post("/api/device/register", json={"device_id": "AUTH_STICK_BOTH_PATHS"})
    assert reg.status_code == 201

    checkin = client.post(
        "/api/device/data",
        json={
            "device_id": "AUTH_STICK_BOTH_PATHS",
            "battery": 60,
            "latitude": 15.86,
            "longitude": 74.51,
            "status": "moving",
        },
    )
    assert checkin.status_code == 200

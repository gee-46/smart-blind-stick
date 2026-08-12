"""Tests for the device check-in and status endpoints."""


def test_device_data_creates_new_device(client):
    payload = {
        "device_id": "STICK_NEW",
        "battery": 82,
        "latitude": 15.8497,
        "longitude": 74.4977,
        "status": "safe",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["device_id"] == "STICK_NEW"


def test_device_data_updates_existing_device(client, registered_device):
    payload = {
        "device_id": registered_device,
        "battery": 55,
        "latitude": 15.85,
        "longitude": 74.50,
        "status": "moving",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 200

    status_response = client.get(f"/api/device/status/{registered_device}")
    assert status_response.status_code == 200
    assert status_response.json()["battery"] == 55


def test_device_status_online_after_checkin(client, registered_device):
    response = client.get(f"/api/device/status/{registered_device}")
    assert response.status_code == 200
    body = response.json()
    assert body["device_id"] == registered_device
    assert body["online"] is True
    assert body["gps_available"] is True
    assert body["last_seen"] is not None


def test_device_status_unknown_device_returns_404(client):
    response = client.get("/api/device/status/DOES_NOT_EXIST")
    assert response.status_code == 404


def test_device_data_rejects_invalid_battery(client):
    payload = {
        "device_id": "STICK_BAD",
        "battery": 150,  # invalid: > 100
        "latitude": 15.8497,
        "longitude": 74.4977,
        "status": "safe",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 422


def test_device_data_rejects_invalid_coordinates(client):
    payload = {
        "device_id": "STICK_BAD_GPS",
        "battery": 50,
        "latitude": 999,  # invalid: out of range
        "longitude": 74.4977,
        "status": "safe",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 422


def test_device_data_missing_field(client):
    payload = {
        "device_id": "STICK_MISSING",
        "battery": 50,
        # missing latitude/longitude
        "status": "safe",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 422

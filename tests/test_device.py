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


def test_wifi_config_post_and_get(client):
    payload = {
        "device_id": "STICK_TEST_WIFI",
        "ssid": "Test-Network",
        "password": "secretpassword",
        "stick_ip": "192.168.1.100",
        "mode": "station",
    }
    res = client.post("/api/device/wifi-config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["device_id"] == "STICK_TEST_WIFI"
    assert data["ssid"] == "Test-Network"

    # Get config (password masked)
    get_res = client.get("/api/device/wifi-config")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["device_id"] == "STICK_TEST_WIFI"
    assert get_data["ssid"] == "Test-Network"
    assert get_data["password_masked"] == "********"


def test_wifi_scan_networks(client):
    res = client.get("/api/device/wifi-scan")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "networks" in data
    assert len(data["networks"]) > 0


def test_ping_hardware_unreachable(client):
    payload = {
        "stick_ip": "127.0.0.1:54321",
        "timeout_seconds": 0.5,
    }
    res = client.post("/api/device/ping-hardware", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["reachable"] is False


def test_ble_telemetry_standard_and_events(client):
    # 1. Normal telemetry
    payload = {
        "device_id": "STICK_BLE_01",
        "battery": 92.0,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_cm": 150.0,
        "obstacle_level": "NONE",
        "fall_detected": False,
        "sos_active": False,
    }
    res = client.post("/api/device/ble-telemetry", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["is_online"] is True
    assert body["battery"] == 92.0

    # 2. Obstacle alert via BLE
    obstacle_payload = {
        "device_id": "STICK_BLE_01",
        "battery": 90.0,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_cm": 35.0,
        "obstacle_level": "CRITICAL",
        "fall_detected": False,
        "sos_active": False,
    }
    res_obs = client.post("/api/device/ble-telemetry", json=obstacle_payload)
    assert res_obs.status_code == 200

    # 3. Fall detected via BLE
    fall_payload = {
        "device_id": "STICK_BLE_01",
        "battery": 89.0,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "distance_cm": 0.0,
        "fall_detected": True,
        "sos_active": False,
    }
    res_fall = client.post("/api/device/ble-telemetry", json=fall_payload)
    assert res_fall.status_code == 200

    # 4. SOS active via BLE
    sos_payload = {
        "device_id": "STICK_BLE_01",
        "battery": 88.0,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "fall_detected": False,
        "sos_active": True,
    }
    res_sos = client.post("/api/device/ble-telemetry", json=sos_payload)
    assert res_sos.status_code == 200


def test_hardware_connectivity_status(client):
    res = client.get("/api/device/connectivity-status")
    assert res.status_code == 200
    data = res.json()
    assert "device_id" in data
    assert "bluetooth" in data
    assert "wifi" in data
    assert "overall_online" in data


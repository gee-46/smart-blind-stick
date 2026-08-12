"""Tests for the GPS/location endpoints."""


def test_get_latest_location(client, registered_device):
    response = client.get(f"/api/location/{registered_device}")
    assert response.status_code == 200
    body = response.json()
    assert body["device_id"] == registered_device
    assert isinstance(body["latitude"], float)
    assert isinstance(body["longitude"], float)


def test_location_history_accumulates(client, registered_device):
    for lat, lng in [(15.86, 74.50), (15.87, 74.51)]:
        client.post(
            "/api/device/data",
            json={
                "device_id": registered_device,
                "battery": 70,
                "latitude": lat,
                "longitude": lng,
                "status": "moving",
            },
        )

    response = client.get(f"/api/location/{registered_device}/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) >= 3  # 1 from fixture + 2 above
    for point in history:
        assert "latitude" in point
        assert "longitude" in point
        assert "timestamp" in point


def test_location_history_limit(client, registered_device):
    response = client.get(f"/api/location/{registered_device}/history?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_real_gps_fields_flow_through_checkin_to_location(client, registered_device):
    """
    A check-in from real GPS hardware (scripts/gps_device_client.py)
    includes altitude/speed/satellites/fix_quality -- confirm these are
    stored and returned, not just latitude/longitude.
    """
    payload = {
        "device_id": registered_device,
        "battery": 88,
        "latitude": 15.86,
        "longitude": 74.51,
        "status": "moving",
        "altitude": 545.4,
        "speed_kmh": 12.3,
        "satellites": 8,
        "fix_quality": 1,
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 200

    location = client.get(f"/api/location/{registered_device}").json()
    assert location["altitude"] == 545.4
    assert location["speed_kmh"] == 12.3
    assert location["satellites"] == 8
    assert location["fix_quality"] == 1

    status = client.get(f"/api/device/status/{registered_device}").json()
    assert status["last_fix_quality"] == 1
    assert status["last_satellites"] == 8


def test_checkin_without_real_gps_fields_still_works(client):
    """Mock/simulated check-ins that omit the real-GPS fields must still work."""
    payload = {
        "device_id": "STICK_MOCK_ONLY",
        "battery": 90,
        "latitude": 15.85,
        "longitude": 74.50,
        "status": "safe",
    }
    response = client.post("/api/device/data", json=payload)
    assert response.status_code == 200

    location = client.get("/api/location/STICK_MOCK_ONLY").json()
    assert location["altitude"] is None
    assert location["satellites"] is None


def test_location_unknown_device_returns_404(client):
    response = client.get("/api/location/DOES_NOT_EXIST")
    assert response.status_code == 404


def test_location_history_unknown_device_returns_404(client):
    response = client.get("/api/location/DOES_NOT_EXIST/history")
    assert response.status_code == 404

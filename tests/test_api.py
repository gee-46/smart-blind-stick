"""Base API Tests covering device check-in, location tracking, and generic events."""
from datetime import date


def test_health_check(client):
    """Test health check endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    res = client.get("/")
    assert res.status_code == 200
    assert "version" in res.json()


def test_device_checkin_and_status(client):
    """Test device check-in and status queries."""
    payload = {
        "device_id": "STICK_BASE_001",
        "battery": 94.5,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "gps_available": True,
    }
    res = client.post("/api/device/data", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["battery"] == 94.5

    # Check status
    res_st = client.get("/api/device/status/STICK_BASE_001")
    assert res_st.status_code == 200
    st_data = res_st.json()
    assert st_data["battery"] == 94.5
    assert st_data["is_online"] is True
    assert st_data["last_latitude"] == 12.9716


def test_location_latest_and_history(client):
    """Test location tracking and history breadcrumbs."""
    device_id = "STICK_LOC_001"
    # Send multiple locations
    coords = [(12.9716, 77.5946), (12.9720, 77.5950), (12.9725, 77.5955)]
    for lat, lon in coords:
        client.post("/api/device/data", json={"device_id": device_id, "latitude": lat, "longitude": lon})

    # Latest location
    res_loc = client.get(f"/api/location/{device_id}")
    assert res_loc.status_code == 200
    assert res_loc.json()["latitude"] == 12.9725
    assert "maps.google.com" in res_loc.json()["maps_url"]

    # Location History
    res_hist = client.get(f"/api/location/{device_id}/history")
    assert res_hist.status_code == 200
    hist = res_hist.json()
    assert hist["count"] == 3


def test_generic_event_ingestion_and_filtering(client):
    """Test multi-subsystem generic event reporting and query filters."""
    device_id = "STICK_EVT_001"

    # 1. Sensor fusion obstacle event
    client.post("/api/events", json={
        "device_id": device_id,
        "source": "sensor_fusion",
        "event_type": "obstacle",
        "risk_level": "medium",
        "message": "Obstacle detected 1.2m ahead",
        "extra": {"distance": 1.2, "sensor": "ultrasonic"},
    })

    # 2. AI Vision object event
    client.post("/api/events", json={
        "device_id": device_id,
        "source": "ai_vision",
        "event_type": "object_detected",
        "risk_level": "high",
        "message": "Approaching vehicle on right",
        "extra": {"object": "car", "confidence": 0.95},
    })

    # Query events
    res = client.get(f"/api/events/{device_id}")
    assert res.status_code == 200
    assert res.json()["count"] == 2

    # Filter by risk_level
    res_high = client.get(f"/api/events/{device_id}?risk_level=high")
    assert res_high.status_code == 200
    assert res_high.json()["count"] == 1
    assert res_high.json()["events"][0]["source"] == "ai_vision"

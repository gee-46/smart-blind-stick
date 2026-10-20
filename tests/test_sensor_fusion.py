"""Tests for Sensor Fusion obstacle evaluation and dashboard endpoint."""


def test_dashboard_endpoint(client):
    """Test dashboard HTML page is served."""
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Smart Blind Stick" in res.text
    assert "Leaflet" in res.text


def test_sensor_fusion_obstacle_detection(client):
    """Test multi-sensor proximity evaluation and haptic/buzzer feedback."""
    payload = {
        "device_id": "STICK_FUSION_001",
        "ultrasonic_cm": 35.0,  # Critical < 40cm
        "battery": 92.0,
    }
    res = client.post("/api/sensors/data", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "critical"
    assert data["obstacle_detected"] is True
    assert data["vibration_feedback"] == "continuous"
    assert data["buzzer_feedback"] == "alarm"
    assert data["nearest_distance_m"] == 0.35


def test_sensor_fusion_clear_path(client):
    """Test clear path assessment when distance is large."""
    payload = {
        "device_id": "STICK_FUSION_002",
        "ultrasonic_cm": 250.0,  # > 200cm
        "battery": 95.0,
    }
    res = client.post("/api/sensors/data", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "low"
    assert data["vibration_feedback"] == "none"
    assert data["buzzer_feedback"] == "silent"


def test_sensor_fusion_ground_ir_dropoff(client):
    """Test ground IR step-down / staircase / puddle detection."""
    payload = {
        "device_id": "STICK_FUSION_003",
        "ground_ir_detected": True,
        "ultrasonic_cm": 150.0,
    }
    res = client.post("/api/sensors/data", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "high"
    assert "Drop-off" in data["summary"]
    assert data["vibration_feedback"] == "pulse_fast"

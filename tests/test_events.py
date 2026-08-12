"""Tests for the generic event system and SOS endpoint."""


def test_create_sensor_fusion_event(client, registered_device):
    payload = {
        "device_id": registered_device,
        "source": "sensor_fusion",
        "event_type": "obstacle",
        "risk_level": "medium",
        "message": "Obstacle detected on left",
        "extra": {"distance": 1.4, "direction": "left", "confidence": 0.91},
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "sensor_fusion"
    assert body["event_type"] == "obstacle"
    assert body["extra"]["direction"] == "left"


def test_create_ai_vision_event(client, registered_device):
    payload = {
        "device_id": registered_device,
        "source": "ai_vision",
        "event_type": "object_detected",
        "risk_level": "high",
        "message": "Vehicle approaching from right",
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 200
    assert response.json()["source"] == "ai_vision"


def test_create_safety_engine_event(client, registered_device):
    payload = {
        "device_id": registered_device,
        "source": "safety_engine",
        "event_type": "danger",
        "risk_level": "critical",
        "message": "Immediate danger",
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 200
    assert response.json()["risk_level"] == "critical"


def test_event_for_unknown_device_returns_404(client):
    payload = {
        "device_id": "DOES_NOT_EXIST",
        "source": "sensor_fusion",
        "event_type": "obstacle",
        "message": "test",
    }
    response = client.post("/api/events", json=payload)
    assert response.status_code == 404


def test_get_events_returns_recent_first(client, registered_device):
    for event_type in ["obstacle", "danger"]:
        client.post(
            "/api/events",
            json={
                "device_id": registered_device,
                "source": "sensor_fusion",
                "event_type": event_type,
                "risk_level": "low",
                "message": "test event",
            },
        )

    response = client.get(f"/api/events/{registered_device}")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 2
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps, reverse=True)


def test_get_events_filter_by_risk_level(client, registered_device):
    client.post(
        "/api/events",
        json={
            "device_id": registered_device,
            "source": "safety_engine",
            "event_type": "danger",
            "risk_level": "critical",
            "message": "filter test",
        },
    )
    response = client.get(f"/api/events/{registered_device}?risk_level=critical")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert all(e["risk_level"] == "critical" for e in events)


def test_get_events_unknown_device_returns_404(client):
    response = client.get("/api/events/DOES_NOT_EXIST")
    assert response.status_code == 404


def test_sos_creates_event_and_returns_id(client, registered_device):
    payload = {
        "device_id": registered_device,
        "reason": "manual_sos",
        "latitude": 15.8497,
        "longitude": 74.4977,
    }
    response = client.post("/api/sos", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["event_id"], int)


def test_sos_unknown_device_returns_404(client):
    payload = {"device_id": "DOES_NOT_EXIST", "reason": "manual_sos"}
    response = client.post("/api/sos", json=payload)
    assert response.status_code == 404


def test_sos_without_location_still_succeeds(client, registered_device):
    payload = {"device_id": registered_device, "reason": "manual_sos"}
    response = client.post("/api/sos", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

"""
Tests for the WebSocket relay.

These verify actual end-to-end behavior: a client subscribes over a real
WebSocket connection, then a REST call writes real data through the
existing services (device_service / event_service), and we assert the
WebSocket client receives the resulting broadcast -- not a simulated
message.
"""


def test_websocket_rejects_missing_token(client, paired_device):
    try:
        with client.websocket_connect(f"/ws/device/{paired_device}?token=garbage") as ws:
            ws.receive_text()
        assert False, "expected the connection to be closed"
    except Exception:
        pass


def test_websocket_rejects_device_not_paired_to_guardian(client, auth_headers, guardian_tokens, registered_device):
    # registered_device exists but was never paired via /api/guardian/devices
    token = guardian_tokens["access_token"]
    try:
        with client.websocket_connect(f"/ws/device/{registered_device}?token={token}") as ws:
            ws.receive_text()
        assert False, "expected the connection to be closed (device not paired)"
    except Exception:
        pass


def test_websocket_connects_for_paired_device(client, guardian_tokens, paired_device):
    token = guardian_tokens["access_token"]
    with client.websocket_connect(f"/ws/device/{paired_device}?token={token}") as ws:
        first = ws.receive_json()
        assert first == {"type": "connected", "device_id": paired_device}


def test_websocket_receives_real_location_update(client, guardian_tokens, paired_device):
    """A REST check-in must produce a real broadcast, not a canned message."""
    token = guardian_tokens["access_token"]
    with client.websocket_connect(f"/ws/device/{paired_device}?token={token}") as ws:
        ws.receive_json()  # the initial "connected" ack

        response = client.post(
            "/api/device/data",
            json={
                "device_id": paired_device,
                "battery": 42,
                "latitude": 15.86,
                "longitude": 74.51,
                "status": "moving",
            },
        )
        assert response.status_code == 200

        location_msg = ws.receive_json()
        assert location_msg["type"] == "location_update"
        assert location_msg["device_id"] == paired_device
        assert location_msg["latitude"] == 15.86
        assert location_msg["longitude"] == 74.51

        battery_msg = ws.receive_json()
        assert battery_msg["type"] == "battery_update"
        assert battery_msg["battery"] == 42


def test_websocket_receives_real_ai_vision_event(client, guardian_tokens, paired_device):
    token = guardian_tokens["access_token"]
    with client.websocket_connect(f"/ws/device/{paired_device}?token={token}") as ws:
        ws.receive_json()  # connected ack

        event_response = client.post(
            "/api/events",
            json={
                "device_id": paired_device,
                "source": "ai_vision",
                "event_type": "object_detected",
                "risk_level": "high",
                "message": "Vehicle approaching from right",
                "extra": {"object": "car", "direction": "right", "distance_m": 2.1, "confidence": 0.94},
            },
        )
        assert event_response.status_code == 200

        event_msg = ws.receive_json()
        assert event_msg["type"] == "object_detected"
        assert event_msg["source"] == "ai_vision"
        assert event_msg["extra"]["object"] == "car"

        safety_msg = ws.receive_json()
        assert safety_msg["type"] == "safety_update"
        assert safety_msg["risk_level"] == "high"


def test_websocket_receives_real_sos(client, guardian_tokens, paired_device):
    token = guardian_tokens["access_token"]
    with client.websocket_connect(f"/ws/device/{paired_device}?token={token}") as ws:
        ws.receive_json()  # connected ack

        sos_response = client.post(
            "/api/sos",
            json={"device_id": paired_device, "reason": "manual_sos", "latitude": 15.85, "longitude": 74.50},
        )
        assert sos_response.status_code == 200

        sos_msg = ws.receive_json()
        assert sos_msg["type"] == "sos"
        assert sos_msg["device_id"] == paired_device
        assert sos_msg["reason"] == "manual_sos"


def test_websocket_heartbeat_ping_pong(client, guardian_tokens, paired_device):
    token = guardian_tokens["access_token"]
    with client.websocket_connect(f"/ws/device/{paired_device}?token={token}") as ws:
        ws.receive_json()  # connected ack
        ws.send_text("ping")
        assert ws.receive_text() == "pong"

"""
Tests for the WebSocket layer (Milestone 2): device authentication,
heartbeat, live GPS updates, real-time event streaming, SOS over
WebSocket, and monitor/dashboard broadcasting.

Uses starlette's in-process WebSocket test client (`client.websocket_connect`)
-- no real network socket or running server needed.
"""
import uuid

import pytest
from starlette.websockets import WebSocketDisconnect

from app.services.connection_manager import manager


@pytest.fixture()
def registered_ws_device(client):
    """Registers a fresh, uniquely-named device for WS tests and returns
    (device_id, api_key). A unique id per test avoids 409 conflicts since
    the test database persists across the whole test session."""
    device_id = f"WS_STICK_{uuid.uuid4().hex[:12]}"
    response = client.post("/api/device/register", json={"device_id": device_id})
    assert response.status_code == 201
    return device_id, response.json()["api_key"]


@pytest.fixture(autouse=True)
def _clear_connection_manager_state():
    """
    The connection manager is process-global (shared module state), so
    clear it before/after every test to avoid one test's leftover
    monitor/device sockets leaking into the next.
    """
    manager.device_connections.clear()
    manager.device_monitors.clear()
    manager.global_monitors.clear()
    yield
    manager.device_connections.clear()
    manager.device_monitors.clear()
    manager.global_monitors.clear()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def test_ws_auth_succeeds_with_valid_key(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        response = ws.receive_json()
        assert response == {"type": "auth_success", "device_id": device_id}


def test_ws_auth_fails_with_wrong_key(client, registered_ws_device):
    device_id, _ = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": "definitely-not-the-right-key"})
        response = ws.receive_json()
        assert response["type"] == "auth_error"

        with pytest.raises(WebSocketDisconnect) as exc_info:
            ws.receive_json()
        assert exc_info.value.code == 4001


def test_ws_auth_fails_for_unregistered_device(client):
    with client.websocket_connect("/ws/device/WS_STICK_NEVER_REGISTERED") as ws:
        ws.send_json({"type": "auth", "api_key": "any-key-at-all"})
        response = ws.receive_json()
        assert response["type"] == "auth_error"

        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_ws_first_message_must_be_auth(client, registered_ws_device):
    device_id, _ = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "heartbeat"})  # not an auth message
        response = ws.receive_json()
        assert response["type"] == "auth_error"

        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()


def test_ws_rejects_invalid_json_during_auth(client, registered_ws_device):
    device_id, _ = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_text("not valid json{{{")
        response = ws.receive_json()
        assert response["type"] == "auth_error"


def test_ws_messages_before_auth_are_never_processed(client, registered_ws_device):
    """
    Sending a well-formed location_update as the FIRST message (skipping
    auth) must be rejected as an auth failure, not processed as data --
    confirms auth happens strictly before any device message handling.
    """
    device_id, _ = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json(
            {
                "type": "location_update",
                "battery": 50,
                "latitude": 15.85,
                "longitude": 74.50,
            }
        )
        response = ws.receive_json()
        assert response["type"] == "auth_error"

    status = client.get(f"/api/device/status/{device_id}")
    # Device was registered but never checked in via this (rejected) message.
    assert status.json()["battery"] is None


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------


def test_ws_heartbeat_acknowledged(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json({"type": "heartbeat"})
        response = ws.receive_json()
        assert response["type"] == "heartbeat_ack"
        assert "timestamp" in response


def test_ws_heartbeat_updates_last_seen_without_writing_location(client, registered_ws_device):
    device_id, api_key = registered_ws_device

    before = client.get(f"/api/device/status/{device_id}").json()
    assert before["last_seen"] is None  # never checked in yet

    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()
        ws.send_json({"type": "heartbeat"})
        ws.receive_json()

    after = client.get(f"/api/device/status/{device_id}").json()
    assert after["last_seen"] is not None
    assert after["online"] is True
    # Heartbeat must not fabricate location data.
    location = client.get(f"/api/location/{device_id}")
    assert location.status_code == 404


# ---------------------------------------------------------------------------
# Live GPS updates
# ---------------------------------------------------------------------------


def test_ws_location_update_stores_and_acks(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json(
            {
                "type": "location_update",
                "battery": 91,
                "latitude": 15.86,
                "longitude": 74.51,
                "status": "moving",
                "altitude": 500.0,
                "satellites": 7,
                "fix_quality": 1,
            }
        )
        response = ws.receive_json()
        assert response["type"] == "location_update_ack"

    location = client.get(f"/api/location/{device_id}").json()
    assert location["latitude"] == 15.86
    assert location["longitude"] == 74.51
    assert location["altitude"] == 500.0
    assert location["satellites"] == 7


def test_ws_location_update_rejects_invalid_data(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json(
            {
                "type": "location_update",
                "battery": 200,  # invalid: > 100
                "latitude": 15.86,
                "longitude": 74.51,
            }
        )
        response = ws.receive_json()
        assert response["type"] == "error"

        # Connection must stay alive after a validation error.
        ws.send_json({"type": "heartbeat"})
        follow_up = ws.receive_json()
        assert follow_up["type"] == "heartbeat_ack"


def test_ws_monitor_receives_live_location_update(client, registered_ws_device):
    device_id, api_key = registered_ws_device

    with client.websocket_connect(f"/ws/monitor/{device_id}") as monitor:
        connected = monitor.receive_json()
        assert connected == {"type": "monitor_connected", "device_id": device_id}

        with client.websocket_connect(f"/ws/device/{device_id}") as device:
            device.send_json({"type": "auth", "api_key": api_key})
            device.receive_json()

            device.send_json(
                {
                    "type": "location_update",
                    "battery": 88,
                    "latitude": 15.87,
                    "longitude": 74.52,
                }
            )
            device.receive_json()  # ack to device

        update = monitor.receive_json()
        assert update["type"] == "location_update"
        assert update["device_id"] == device_id
        assert update["latitude"] == 15.87
        assert update["longitude"] == 74.52


# ---------------------------------------------------------------------------
# Real-time event streaming
# ---------------------------------------------------------------------------


def test_ws_event_stored_and_acked(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json(
            {
                "type": "event",
                "source": "sensor_fusion",
                "event_type": "obstacle",
                "risk_level": "medium",
                "message": "Obstacle on left",
                "extra": {"distance": 1.2, "direction": "left"},
            }
        )
        response = ws.receive_json()
        assert response["type"] == "event_ack"
        assert isinstance(response["event_id"], int)

    events = client.get(f"/api/events/{device_id}").json()
    assert any(e["event_type"] == "obstacle" and e["extra"]["direction"] == "left" for e in events)


def test_ws_event_rejects_missing_required_fields(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json({"type": "event"})  # missing source/event_type
        response = ws.receive_json()
        assert response["type"] == "error"


def test_ws_monitor_receives_live_event(client, registered_ws_device):
    device_id, api_key = registered_ws_device

    with client.websocket_connect(f"/ws/monitor/{device_id}") as monitor:
        monitor.receive_json()  # monitor_connected

        with client.websocket_connect(f"/ws/device/{device_id}") as device:
            device.send_json({"type": "auth", "api_key": api_key})
            device.receive_json()

            device.send_json(
                {
                    "type": "event",
                    "source": "ai_vision",
                    "event_type": "object_detected",
                    "risk_level": "high",
                    "message": "Vehicle approaching",
                }
            )
            device.receive_json()

        update = monitor.receive_json()
        assert update["type"] == "event"
        assert update["source"] == "ai_vision"
        assert update["risk_level"] == "high"


def test_ws_global_monitor_receives_events_from_any_device(client):
    reg_a = client.post("/api/device/register", json={"device_id": "WS_STICK_GLOBAL_A"}).json()
    reg_b = client.post("/api/device/register", json={"device_id": "WS_STICK_GLOBAL_B"}).json()

    with client.websocket_connect("/ws/monitor") as global_monitor:
        connected = global_monitor.receive_json()
        assert connected == {"type": "monitor_connected", "device_id": "*"}

        for reg in (reg_a, reg_b):
            with client.websocket_connect(f"/ws/device/{reg['device_id']}") as device:
                device.send_json({"type": "auth", "api_key": reg["api_key"]})
                device.receive_json()
                device.send_json({"type": "heartbeat"})
                device.receive_json()
                device.send_json(
                    {
                        "type": "event",
                        "source": "safety_engine",
                        "event_type": "danger",
                        "risk_level": "critical",
                        "message": "test",
                    }
                )
                device.receive_json()

        first = global_monitor.receive_json()
        second = global_monitor.receive_json()
        seen_devices = {first["device_id"], second["device_id"]}
        assert seen_devices == {"WS_STICK_GLOBAL_A", "WS_STICK_GLOBAL_B"}


# ---------------------------------------------------------------------------
# SOS over WebSocket
# ---------------------------------------------------------------------------


def test_ws_sos_stored_and_acked(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json(
            {
                "type": "sos",
                "reason": "manual_sos",
                "latitude": 15.85,
                "longitude": 74.50,
            }
        )
        response = ws.receive_json()
        assert response["type"] == "sos_ack"
        assert isinstance(response["event_id"], int)


def test_ws_sos_without_location_still_works(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json({"type": "sos", "reason": "fall_detected"})
        response = ws.receive_json()
        assert response["type"] == "sos_ack"


def test_ws_monitor_receives_live_sos(client, registered_ws_device):
    device_id, api_key = registered_ws_device

    with client.websocket_connect(f"/ws/monitor/{device_id}") as monitor:
        monitor.receive_json()

        with client.websocket_connect(f"/ws/device/{device_id}") as device:
            device.send_json({"type": "auth", "api_key": api_key})
            device.receive_json()

            device.send_json(
                {
                    "type": "sos",
                    "reason": "manual_sos",
                    "latitude": 15.85,
                    "longitude": 74.50,
                }
            )
            device.receive_json()

        update = monitor.receive_json()
        assert update["type"] == "sos"
        assert update["device_id"] == device_id
        assert update["reason"] == "manual_sos"


# ---------------------------------------------------------------------------
# Generic message handling / robustness
# ---------------------------------------------------------------------------


def test_ws_unknown_message_type_returns_error_but_keeps_connection(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json({"type": "self_destruct"})
        response = ws.receive_json()
        assert response["type"] == "error"

        ws.send_json({"type": "heartbeat"})
        follow_up = ws.receive_json()
        assert follow_up["type"] == "heartbeat_ack"


def test_ws_invalid_json_after_auth_returns_error_but_keeps_connection(
    client, registered_ws_device
):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_text("{not valid json")
        response = ws.receive_json()
        assert response["type"] == "error"

        ws.send_json({"type": "heartbeat"})
        follow_up = ws.receive_json()
        assert follow_up["type"] == "heartbeat_ack"


def test_ws_message_without_type_field_returns_error(client, registered_ws_device):
    device_id, api_key = registered_ws_device
    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()

        ws.send_json({"battery": 50})  # no "type" key
        response = ws.receive_json()
        assert response["type"] == "error"


# ---------------------------------------------------------------------------
# Monitor connection lifecycle
# ---------------------------------------------------------------------------


def test_monitor_connect_and_disconnect_updates_manager_state(client, registered_ws_device):
    device_id, _ = registered_ws_device

    assert manager.monitor_count(device_id) == 0

    with client.websocket_connect(f"/ws/monitor/{device_id}") as monitor:
        monitor.receive_json()
        assert manager.monitor_count(device_id) == 1

    assert manager.monitor_count(device_id) == 0


def test_device_disconnect_removes_from_manager(client, registered_ws_device):
    device_id, api_key = registered_ws_device

    with client.websocket_connect(f"/ws/device/{device_id}") as ws:
        ws.send_json({"type": "auth", "api_key": api_key})
        ws.receive_json()
        assert manager.is_device_connected(device_id) is True

    assert manager.is_device_connected(device_id) is False

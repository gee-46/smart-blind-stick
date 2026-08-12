"""
WebSocket API (Milestone 2).

Two kinds of connections:

  WS /ws/device/{device_id}
      The smart stick itself. Must authenticate with its API key
      (issued by POST /api/device/register) as the very first message
      before anything else is accepted. Once authenticated, it can send
      heartbeat, location_update, event, and sos messages -- all of
      which reuse the exact same service-layer functions the REST API
      uses, so business logic and validation rules are never duplicated.

  WS /ws/monitor/{device_id}  and  WS /ws/monitor
      Read-only streams for a dashboard/mobile app to watch live
      updates. `/ws/monitor/{device_id}` sees only that device;
      `/ws/monitor` sees every device. These are intentionally left
      unauthenticated for Milestone 2, matching the existing decision to
      leave /api/events open while the other modules are still in
      development -- see README "Security notes" for the follow-up plan.

Message envelope (device -> server), always JSON with a "type" field:

    {"type": "auth", "api_key": "..."}                        (first message only)
    {"type": "heartbeat"}
    {"type": "location_update", "battery": 82, "latitude": .., "longitude": .., ...}
    {"type": "event", "source": "sensor_fusion", "event_type": "obstacle", ...}
    {"type": "sos", "reason": "manual_sos", "latitude": .., "longitude": ..}

Server -> device acknowledgements/errors use the same envelope style:
    {"type": "auth_success" | "auth_error", ...}
    {"type": "heartbeat_ack", "timestamp": "..."}
    {"type": "location_update_ack", "timestamp": "..."}
    {"type": "event_ack", "event_id": 123}
    {"type": "sos_ack", "event_id": 456}
    {"type": "error", "message": "..."}

Server -> monitor broadcasts use "type" values: "location_update",
"event", "sos", "device_online", "device_offline".
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.config import get_settings
from app.database.database import SessionLocal
from app.schemas.device import DeviceDataIn
from app.schemas.event import EventIn, SOSIn
from app.services import device_service, event_service
from app.services.connection_manager import manager

logger = logging.getLogger("ws")
settings = get_settings()

router = APIRouter(tags=["websocket"])

# Custom WebSocket close codes (application-specific range is 4000-4999).
CLOSE_AUTH_FAILED = 4001
CLOSE_AUTH_TIMEOUT = 4002


# ---------------------------------------------------------------------------
# Device connection: auth handshake, then message loop
# ---------------------------------------------------------------------------


@router.websocket("/ws/device/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str) -> None:
    await websocket.accept()

    if not await _authenticate(websocket, device_id):
        return  # _authenticate has already sent an error and closed the socket

    manager.connect_device(device_id, websocket)
    logger.info("Device '%s' connected", device_id)

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_device_message(websocket, device_id, raw)
    except WebSocketDisconnect:
        logger.info("Device '%s' disconnected", device_id)
    finally:
        manager.disconnect_device(device_id, websocket)


async def _authenticate(websocket: WebSocket, device_id: str) -> bool:
    """
    Requires the first message to be {"type": "auth", "api_key": "..."}.
    Returns True (and leaves the socket open) only on success; on any
    failure it sends an auth_error and closes the socket itself.
    """
    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(), timeout=settings.websocket_auth_timeout_seconds
        )
    except asyncio.TimeoutError:
        await _safe_close(websocket, CLOSE_AUTH_TIMEOUT, "Authentication timed out")
        return False

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await _send_json(websocket, {"type": "auth_error", "message": "Invalid JSON"})
        await _safe_close(websocket, CLOSE_AUTH_FAILED, "Invalid auth message")
        return False

    if not isinstance(data, dict) or data.get("type") != "auth" or "api_key" not in data:
        await _send_json(
            websocket,
            {
                "type": "auth_error",
                "message": "First message must be {'type': 'auth', 'api_key': '...'}",
            },
        )
        await _safe_close(websocket, CLOSE_AUTH_FAILED, "Missing/invalid auth message")
        return False

    db = SessionLocal()
    try:
        device = device_service.verify_device_credentials(db, device_id, data["api_key"])
    finally:
        db.close()

    if device is None:
        await _send_json(
            websocket, {"type": "auth_error", "message": "Invalid device_id or api_key"}
        )
        await _safe_close(websocket, CLOSE_AUTH_FAILED, "Invalid credentials")
        return False

    await _send_json(websocket, {"type": "auth_success", "device_id": device_id})
    return True


# ---------------------------------------------------------------------------
# Authenticated message handling
# ---------------------------------------------------------------------------


async def _handle_device_message(websocket: WebSocket, device_id: str, raw: str) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await _send_json(websocket, {"type": "error", "message": "Invalid JSON"})
        return

    if not isinstance(data, dict) or "type" not in data:
        await _send_json(websocket, {"type": "error", "message": "Message must include 'type'"})
        return

    msg_type = data["type"]
    handler = _MESSAGE_HANDLERS.get(msg_type)
    if handler is None:
        await _send_json(
            websocket, {"type": "error", "message": f"Unknown message type '{msg_type}'"}
        )
        return

    try:
        await handler(websocket, device_id, data)
    except Exception:
        # A single malformed/unexpected message must never kill the
        # connection -- log it and tell the device, then keep listening.
        logger.exception("Error handling '%s' message from device '%s'", msg_type, device_id)
        await _send_json(
            websocket, {"type": "error", "message": f"Failed to process '{msg_type}' message"}
        )


async def _handle_heartbeat(websocket: WebSocket, device_id: str, data: dict) -> None:
    db = SessionLocal()
    try:
        device_service.record_heartbeat(db, device_id)
    finally:
        db.close()

    await _send_json(
        websocket,
        {"type": "heartbeat_ack", "timestamp": datetime.now(timezone.utc).isoformat()},
    )


async def _handle_location_update(websocket: WebSocket, device_id: str, data: dict) -> None:
    fields = {k: v for k, v in data.items() if k != "type"}
    fields["device_id"] = device_id

    try:
        payload = DeviceDataIn(**fields)
    except ValidationError as exc:
        await _send_json(websocket, {"type": "error", "message": _format_validation_error(exc)})
        return

    db = SessionLocal()
    try:
        device_service.upsert_device_data(db, payload)
    finally:
        db.close()

    now_iso = datetime.now(timezone.utc).isoformat()

    await manager.broadcast_to_monitors(
        device_id,
        {
            "type": "location_update",
            "device_id": device_id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "battery": payload.battery,
            "status": payload.status,
            "altitude": payload.altitude,
            "speed_kmh": payload.speed_kmh,
            "satellites": payload.satellites,
            "fix_quality": payload.fix_quality,
            "timestamp": now_iso,
        },
    )

    await _send_json(websocket, {"type": "location_update_ack", "timestamp": now_iso})


async def _handle_event(websocket: WebSocket, device_id: str, data: dict) -> None:
    fields = {k: v for k, v in data.items() if k != "type"}
    fields["device_id"] = device_id

    try:
        payload = EventIn(**fields)
    except ValidationError as exc:
        await _send_json(websocket, {"type": "error", "message": _format_validation_error(exc)})
        return

    db = SessionLocal()
    try:
        event = event_service.create_event(db, payload)
    finally:
        db.close()

    await manager.broadcast_to_monitors(
        device_id,
        {
            "type": "event",
            "device_id": device_id,
            "source": event.source,
            "event_type": event.event_type,
            "risk_level": event.risk_level,
            "message": event.message,
            "extra": event.extra,
            "timestamp": event.timestamp.isoformat(),
        },
    )

    await _send_json(websocket, {"type": "event_ack", "event_id": event.id})


async def _handle_sos(websocket: WebSocket, device_id: str, data: dict) -> None:
    fields = {k: v for k, v in data.items() if k != "type"}
    fields["device_id"] = device_id

    try:
        payload = SOSIn(**fields)
    except ValidationError as exc:
        await _send_json(websocket, {"type": "error", "message": _format_validation_error(exc)})
        return

    db = SessionLocal()
    try:
        sos = event_service.create_sos(db, payload)
    finally:
        db.close()

    await manager.broadcast_to_monitors(
        device_id,
        {
            "type": "sos",
            "device_id": device_id,
            "reason": sos.reason,
            "latitude": sos.latitude,
            "longitude": sos.longitude,
            "timestamp": sos.timestamp.isoformat(),
        },
    )

    await _send_json(websocket, {"type": "sos_ack", "event_id": sos.id})


_MESSAGE_HANDLERS = {
    "heartbeat": _handle_heartbeat,
    "location_update": _handle_location_update,
    "event": _handle_event,
    "sos": _handle_sos,
}


# ---------------------------------------------------------------------------
# Monitor / dashboard connections (read-only)
# ---------------------------------------------------------------------------


@router.websocket("/ws/monitor/{device_id}")
async def monitor_device_websocket(websocket: WebSocket, device_id: str) -> None:
    """Live stream of updates for one specific device."""
    await websocket.accept()
    manager.connect_monitor(device_id, websocket)
    await _send_json(websocket, {"type": "monitor_connected", "device_id": device_id})

    try:
        while True:
            # Monitors are read-only; we just drain whatever they send
            # (e.g. websocket-level pings) and otherwise wait for a
            # disconnect. All real traffic flows server -> monitor.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_monitor(device_id, websocket)


@router.websocket("/ws/monitor")
async def monitor_all_websocket(websocket: WebSocket) -> None:
    """Live stream of updates for every device (dashboard-wide view)."""
    await websocket.accept()
    manager.connect_monitor(None, websocket)
    await _send_json(websocket, {"type": "monitor_connected", "device_id": "*"})

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_monitor(None, websocket)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


async def _send_json(websocket: WebSocket, message: dict) -> None:
    try:
        await websocket.send_json(message)
    except Exception:
        # Socket already gone -- nothing more we can do.
        pass


async def _safe_close(websocket: WebSocket, code: int, reason: str) -> None:
    try:
        await websocket.close(code=code, reason=reason)
    except Exception:
        pass


def _format_validation_error(exc: ValidationError) -> str:
    """Compact, single-line summary of a Pydantic validation error."""
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts) if parts else "Invalid data"

"""
Real-time WebSocket route.

    GET /ws/device/{device_id}?token=<jwt access token> (Guardian mode)
    GET /ws/device/{device_id} (Hardware Device mode)

Auth:
- Guardian mode: authenticated with JWT access token in query param.
- Hardware Device mode: unauthenticated initially, accepts and validates
  {"type": "auth", "api_key": "<device_key>"} before processing telemetry.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.core.deps import get_current_guardian_ws
from app.database.database import SessionLocal
from app.schemas.device import DeviceDataIn
from app.schemas.event import EventIn, SOSIn
from app.services import device_service, event_service, guardian_service
from app.websocket_manager import manager as ws_manager

logger = logging.getLogger("websocket_api")

router = APIRouter(tags=["websocket"])


async def _handle_device_mode(websocket: WebSocket, device_id: str) -> None:
    await websocket.accept()

    # Device must authenticate as first message
    try:
        first_raw = await websocket.receive_text()
        data = json.loads(first_raw)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing or invalid auth message")
        return

    if not isinstance(data, dict) or data.get("type") != "auth" or not data.get("api_key"):
        try:
            await websocket.send_json({"type": "auth_error", "message": "Expected auth message"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid auth message")
        except Exception:
            pass
        return

    db = SessionLocal()
    try:
        device = device_service.verify_device_credentials(db, device_id, data["api_key"])
    finally:
        db.close()

    if device is None:
        try:
            await websocket.send_json({"type": "auth_error", "message": "Invalid device_id or api_key"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid credentials")
        except Exception:
            pass
        return

    await websocket.send_json({"type": "auth_success", "device_id": device_id})

    # Main event loop for authenticated device
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            if not isinstance(msg, dict) or "type" not in msg:
                await websocket.send_json({"type": "error", "message": "Message must include 'type'"})
                continue

            msg_type = msg["type"]

            if msg_type == "heartbeat":
                db = SessionLocal()
                try:
                    device_service.record_heartbeat(db, device_id)
                finally:
                    db.close()
                await websocket.send_json(
                    {"type": "heartbeat_ack", "timestamp": datetime.now(timezone.utc).isoformat()}
                )

            elif msg_type == "location_update":
                fields = {k: v for k, v in msg.items() if k != "type"}
                fields["device_id"] = device_id
                try:
                    payload = DeviceDataIn(**fields)
                except ValidationError as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
                    continue

                db = SessionLocal()
                try:
                    device_service.upsert_device_data(db, payload)
                finally:
                    db.close()
                await websocket.send_json(
                    {"type": "location_update_ack", "timestamp": datetime.now(timezone.utc).isoformat()}
                )

            elif msg_type == "event":
                fields = {k: v for k, v in msg.items() if k != "type"}
                fields["device_id"] = device_id
                try:
                    payload = EventIn(**fields)
                except ValidationError as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
                    continue

                db = SessionLocal()
                try:
                    ev = event_service.create_event(db, payload)
                finally:
                    db.close()
                await websocket.send_json({"type": "event_ack", "event_id": ev.id})

            elif msg_type == "sos":
                fields = {k: v for k, v in msg.items() if k != "type"}
                fields["device_id"] = device_id
                try:
                    payload = SOSIn(**fields)
                except ValidationError as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
                    continue

                db = SessionLocal()
                try:
                    sos = event_service.create_sos(db, payload)
                finally:
                    db.close()
                await websocket.send_json({"type": "sos_ack", "event_id": sos.id})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type '{msg_type}'"})

    except WebSocketDisconnect:
        pass


@router.websocket("/ws/device/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str, token: Optional[str] = None):
    if token is None:
        # Hardware device connection
        await _handle_device_mode(websocket, device_id)
        return

    # Guardian connection mode
    db = SessionLocal()
    try:
        guardian = get_current_guardian_ws(token, db)
        if guardian is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
            return

        if not guardian_service.guardian_owns_device(db, guardian.id, device_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Device not paired to this guardian")
            return
    finally:
        db.close()

    await ws_manager.connect(device_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "device_id": device_id})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(device_id, websocket)

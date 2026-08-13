"""
Real-time WebSocket route.

    GET /ws/device/{device_id}?token=<jwt access token>

Auth: the same JWT access token issued by /api/auth/login. Guardians may
only subscribe to devices they've actually paired (per
app/services/guardian_service.guardian_owns_device) -- this mirrors the
REST authorization model, so a stolen device_id alone isn't enough to
snoop on another guardian's stick.

The server never invents events here; it only relays what
device_service/event_service already broadcast via websocket_manager
after writing real rows to the database (see hooks in those modules).
"""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.deps import get_current_guardian_ws
from app.database.database import SessionLocal
from app.services import guardian_service
from app.websocket_manager import manager as ws_manager

logger = logging.getLogger("websocket_api")

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/device/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str, token: str):
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
            # We don't require the client to send anything, but reading
            # keeps the connection alive and lets us detect a clean
            # disconnect. Guardians can send "ping" for an app-level
            # heartbeat (separate from the WebSocket protocol ping/pong).
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(device_id, websocket)

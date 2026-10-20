"""
WebSocket connection manager.

The device/event/SOS services are synchronous (called from sync FastAPI
route handlers, per the existing codebase style), but broadcasting to
WebSocket clients requires the asyncio event loop. We capture the running
loop once at app startup (see app/main.py lifespan) and use
`asyncio.run_coroutine_threadsafe` so sync service code can safely
trigger a broadcast without needing to become async itself.

Real events only: this module never invents/synthesizes data. It only
relays what the device_service/event_service already persisted.
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger("websocket_manager")

# Captured in app/main.py's lifespan on startup.
main_event_loop: asyncio.AbstractEventLoop | None = None


class ConnectionManager:
    def __init__(self) -> None:
        # device_id -> set of active websocket connections subscribed to it
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[device_id].add(websocket)
        logger.info("WebSocket connected for device_id=%s (total=%d)", device_id, len(self._connections[device_id]))

    def disconnect(self, device_id: str, websocket: WebSocket) -> None:
        self._connections[device_id].discard(websocket)
        if not self._connections[device_id]:
            del self._connections[device_id]
        logger.info("WebSocket disconnected for device_id=%s", device_id)

    async def broadcast(self, device_id: str, message: dict) -> None:
        connections = list(self._connections.get(device_id, set()))
        if not connections:
            return
        payload = json.dumps(message, default=str)
        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(device_id, ws)

    def broadcast_sync(self, device_id: str, message: dict) -> None:
        """
        Thread-safe entry point for synchronous service code (e.g.
        device_service.upsert_device_data) to push a real-time event
        without becoming async itself.
        """
        if main_event_loop is None:
            logger.warning("broadcast_sync called before event loop was captured; dropping message")
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(device_id, message), main_event_loop)


manager = ConnectionManager()

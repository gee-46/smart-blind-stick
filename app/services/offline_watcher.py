"""
Background task: polls devices that currently have active WebSocket
subscribers and broadcasts a real `device_offline` event the moment a
device crosses the existing `device_offline_after_seconds` threshold
(the same threshold app/services/device_service.is_device_online already
uses for the REST status endpoint) -- so the dashboard doesn't have to
wait for a manual refresh to find out a stick went silent.
"""
import asyncio
import logging

from app.config import get_settings
from app.database.database import SessionLocal
from app.services import device_service
from app.websocket_manager import manager as ws_manager

logger = logging.getLogger("offline_watcher")
settings = get_settings()

_POLL_INTERVAL_SECONDS = 10
_last_known_online: dict[str, bool] = {}


async def run_offline_watcher() -> None:
    while True:
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)
        device_ids = list(ws_manager._connections.keys())  # only devices someone is watching
        if not device_ids:
            continue

        db = SessionLocal()
        try:
            for device_id in device_ids:
                device = device_service.get_device(db, device_id)
                if device is None:
                    continue
                online_now = device_service.is_device_online(device)
                was_online = _last_known_online.get(device_id, online_now)
                if was_online and not online_now:
                    await ws_manager.broadcast(
                        device_id,
                        {
                            "type": "device_offline",
                            "device_id": device_id,
                            "last_seen": device.last_seen,
                        },
                    )
                elif (not was_online) and online_now:
                    await ws_manager.broadcast(
                        device_id,
                        {
                            "type": "device_online",
                            "device_id": device_id,
                            "last_seen": device.last_seen,
                        },
                    )
                _last_known_online[device_id] = online_now
        finally:
            db.close()

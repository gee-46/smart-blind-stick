"""
Heartbeat monitoring (Milestone 2).

Two complementary pieces:

1. `record_heartbeat` (in device_service) -- called synchronously whenever
   a device sends a WS "heartbeat" or "location_update" message; updates
   last_seen immediately.

2. This module's background scan loop -- periodically walks every known
   device, checks online/offline status via the existing
   `device_service.is_device_online`, and broadcasts a "device_online" /
   "device_offline" message to monitors *only on state transitions* (not
   every tick), so watching dashboards aren't flooded.

`scan_devices_once` is deliberately a plain synchronous function taking a
DB session, with no asyncio/broadcast side effects baked in -- that
keeps it trivial to unit test (call it directly, no timers, no running
event loop needed) while `run_heartbeat_loop` handles the "real" async
scheduling + broadcasting for the running server.
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.database import SessionLocal
from app.models.device import Device
from app.services import device_service
from app.services.connection_manager import manager

logger = logging.getLogger("heartbeat_service")
settings = get_settings()

# In-memory cache of each device's last known online state, so a scan
# only reports *transitions* rather than re-announcing "online" every
# tick. Keyed by device_id.
_last_known_online: dict[str, bool] = {}


def reset_heartbeat_state() -> None:
    """Clears the transition-tracking cache. Used between test runs."""
    _last_known_online.clear()


def scan_devices_once(db: Session) -> list[dict]:
    """
    Checks every device's online/offline state against its previously
    known state and returns the list of transitions that occurred, e.g.:
        [{"device_id": "STICK_001", "online": False}]

    A device seen for the first time by this scan is recorded but not
    reported as a transition (there's no previous state to transition
    from -- avoids a burst of "online" events on server startup).
    """
    transitions = []
    devices = db.query(Device).all()

    for device in devices:
        online = device_service.is_device_online(device)
        previous = _last_known_online.get(device.device_id)

        if previous is None:
            _last_known_online[device.device_id] = online
            continue

        if previous != online:
            _last_known_online[device.device_id] = online
            transitions.append({"device_id": device.device_id, "online": online})

    return transitions


async def broadcast_transitions(transitions: list[dict]) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    for change in transitions:
        await manager.broadcast_to_monitors(
            change["device_id"],
            {
                "type": "device_online" if change["online"] else "device_offline",
                "device_id": change["device_id"],
                "timestamp": now_iso,
            },
        )


async def run_heartbeat_loop(interval_seconds: float | None = None) -> None:
    """
    Runs forever (until cancelled): scans devices, broadcasts any
    online/offline transitions, sleeps, repeats. Started as a background
    asyncio task from the app lifespan (see app/main.py) and cancelled on
    shutdown.
    """
    interval = interval_seconds if interval_seconds is not None else (
        settings.heartbeat_check_interval_seconds
    )

    logger.info("Heartbeat monitor started (interval=%.1fs)", interval)

    while True:
        try:
            db = SessionLocal()
            try:
                transitions = scan_devices_once(db)
            finally:
                db.close()

            if transitions:
                await broadcast_transitions(transitions)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Heartbeat scan failed")

        await asyncio.sleep(interval)

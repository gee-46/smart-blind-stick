"""
In-memory WebSocket connection registry.

Tracks which devices currently have an authenticated WebSocket open, and
which "monitor" (dashboard/mobile-app-to-be) sockets want to receive
live updates -- either for one specific device or for everything.

This is intentionally in-process, in-memory state (a plain dict/set),
not persisted to the database: connections are inherently tied to a
single running server process and don't need to survive a restart. If
this backend is later horizontally scaled across multiple processes,
this would need to move to a shared broker (e.g. Redis pub/sub) --
noted here rather than solved now, since Milestone 2 targets a single
backend instance.
"""
import logging

from starlette.websockets import WebSocket

logger = logging.getLogger("connection_manager")


class ConnectionManager:
    def __init__(self) -> None:
        # One active connection per device_id. A new connection for the
        # same device_id replaces the old entry (the old socket, if still
        # open, is left for its own receive loop to notice the disconnect).
        self.device_connections: dict[str, WebSocket] = {}

        # Monitors watching one specific device.
        self.device_monitors: dict[str, set[WebSocket]] = {}

        # Monitors watching every device (dashboard-wide view).
        self.global_monitors: set[WebSocket] = set()

    # -- Device connections --------------------------------------------

    def connect_device(self, device_id: str, websocket: WebSocket) -> None:
        self.device_connections[device_id] = websocket

    def disconnect_device(self, device_id: str, websocket: WebSocket) -> None:
        if self.device_connections.get(device_id) is websocket:
            del self.device_connections[device_id]

    def is_device_connected(self, device_id: str) -> bool:
        return device_id in self.device_connections

    # -- Monitor connections ---------------------------------------------

    def connect_monitor(self, device_id: str | None, websocket: WebSocket) -> None:
        """`device_id=None` registers a global monitor (sees all devices)."""
        if device_id is None:
            self.global_monitors.add(websocket)
        else:
            self.device_monitors.setdefault(device_id, set()).add(websocket)

    def disconnect_monitor(self, device_id: str | None, websocket: WebSocket) -> None:
        if device_id is None:
            self.global_monitors.discard(websocket)
            return

        monitors = self.device_monitors.get(device_id)
        if monitors is not None:
            monitors.discard(websocket)
            if not monitors:
                del self.device_monitors[device_id]

    def monitor_count(self, device_id: str) -> int:
        return len(self.device_monitors.get(device_id, set())) + len(self.global_monitors)

    # -- Broadcasting ------------------------------------------------------

    async def broadcast_to_monitors(self, device_id: str, message: dict) -> None:
        """
        Sends `message` to every monitor watching `device_id` specifically,
        plus every global monitor. Sockets that fail to send (already
        disconnected but not yet cleaned up) are dropped silently rather
        than raising -- a slow/dead dashboard connection must never break
        device-facing processing.
        """
        targets = list(self.device_monitors.get(device_id, set())) + list(self.global_monitors)
        if not targets:
            return

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.device_monitors.get(device_id, set()).discard(ws)
            self.global_monitors.discard(ws)


# Single shared instance used across the app (imported by app/api/ws.py
# and app/services/heartbeat_service.py).
manager = ConnectionManager()

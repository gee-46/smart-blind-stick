"""
Unit tests for ConnectionManager (Milestone 2) using lightweight fake
WebSocket objects -- no real connections, no app, no DB. Complements
tests/test_websocket.py, which exercises the manager indirectly through
real (in-process) WebSocket connections.

The manager's broadcast method is async, so those tests drive it with
`asyncio.run()` rather than adding a pytest-asyncio dependency for a
handful of tests.
"""
import asyncio

import pytest

from app.services.connection_manager import ConnectionManager


class FakeWebSocket:
    """Minimal stand-in for starlette.websockets.WebSocket."""

    def __init__(self, fail: bool = False):
        self.sent: list[dict] = []
        self.fail = fail

    async def send_json(self, message: dict) -> None:
        if self.fail:
            raise RuntimeError("simulated dead socket")
        self.sent.append(message)


@pytest.fixture()
def mgr():
    return ConnectionManager()


def test_connect_and_disconnect_device(mgr):
    ws = FakeWebSocket()
    assert mgr.is_device_connected("D1") is False

    mgr.connect_device("D1", ws)
    assert mgr.is_device_connected("D1") is True

    mgr.disconnect_device("D1", ws)
    assert mgr.is_device_connected("D1") is False


def test_disconnect_device_ignores_stale_socket():
    """If a newer connection has replaced the old one, disconnecting the
    OLD socket must not remove the NEW one."""
    mgr = ConnectionManager()
    old_ws = FakeWebSocket()
    new_ws = FakeWebSocket()

    mgr.connect_device("D1", old_ws)
    mgr.connect_device("D1", new_ws)  # new connection replaces old
    mgr.disconnect_device("D1", old_ws)  # stale disconnect

    assert mgr.is_device_connected("D1") is True


def test_monitor_count_combines_specific_and_global(mgr):
    specific = FakeWebSocket()
    global_ws = FakeWebSocket()

    mgr.connect_monitor("D1", specific)
    mgr.connect_monitor(None, global_ws)

    assert mgr.monitor_count("D1") == 2
    assert mgr.monitor_count("D2") == 1  # only the global monitor


def test_broadcast_reaches_specific_and_global_monitors(mgr):
    specific = FakeWebSocket()
    global_ws = FakeWebSocket()
    other_device_monitor = FakeWebSocket()

    mgr.connect_monitor("D1", specific)
    mgr.connect_monitor(None, global_ws)
    mgr.connect_monitor("D2", other_device_monitor)

    asyncio.run(mgr.broadcast_to_monitors("D1", {"type": "event", "device_id": "D1"}))

    assert specific.sent == [{"type": "event", "device_id": "D1"}]
    assert global_ws.sent == [{"type": "event", "device_id": "D1"}]
    assert other_device_monitor.sent == []  # not watching D1


def test_broadcast_with_no_monitors_does_nothing(mgr):
    # Should not raise even with zero monitors connected.
    asyncio.run(mgr.broadcast_to_monitors("D1", {"type": "event"}))


def test_broadcast_drops_dead_sockets_without_raising(mgr):
    dead = FakeWebSocket(fail=True)
    alive = FakeWebSocket()

    mgr.connect_monitor("D1", dead)
    mgr.connect_monitor("D1", alive)

    asyncio.run(mgr.broadcast_to_monitors("D1", {"type": "event"}))

    assert alive.sent == [{"type": "event"}]
    assert mgr.monitor_count("D1") == 1  # dead socket was cleaned up


def test_disconnect_monitor_removes_empty_device_entry(mgr):
    ws = FakeWebSocket()
    mgr.connect_monitor("D1", ws)
    assert "D1" in mgr.device_monitors

    mgr.disconnect_monitor("D1", ws)
    assert "D1" not in mgr.device_monitors


def test_disconnect_global_monitor(mgr):
    ws = FakeWebSocket()
    mgr.connect_monitor(None, ws)
    assert ws in mgr.global_monitors

    mgr.disconnect_monitor(None, ws)
    assert ws not in mgr.global_monitors

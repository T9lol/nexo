"""Tests for the UI-5 WebSocket streaming layer.

Split into deterministic ConnectionManager unit tests (fake provider, single
ticks) and real TestClient WebSocket round-trips through the app.
"""

import asyncio
import time
import unittest

from fastapi.testclient import TestClient

import ui.dashboard as dash
from ui.providers import MockDashboardProvider
from ui.ws import ConnectionManager, _signature


class FakeProvider:
    """Snapshot changes only when bump() is called; updated_at always changes."""

    def __init__(self) -> None:
        self._calls = 0
        self._value = 0

    def bump(self) -> None:
        self._value += 1

    def snapshot(self) -> dict:
        self._calls += 1
        return {"updated_at": f"t{self._calls}", "value": self._value, "control": {}}


class ManagerUnitTests(unittest.IsolatedAsyncioTestCase):
    def test_signature_ignores_timestamp(self) -> None:
        a = {"updated_at": "t1", "value": 5}
        b = {"updated_at": "t2", "value": 5}
        c = {"updated_at": "t1", "value": 6}
        self.assertEqual(_signature(a), _signature(b))
        self.assertNotEqual(_signature(a), _signature(c))

    async def test_sequence_monotonic_and_heartbeat(self) -> None:
        provider = FakeProvider()
        manager = ConnectionManager(provider, poll_interval=0.01, heartbeat_interval=0.05)

        first = await manager._tick(now=0.0)
        self.assertEqual(first["type"], "state")
        self.assertEqual(first["sequence"], 1)

        # No change and within heartbeat window -> nothing sent.
        self.assertIsNone(await manager._tick(now=0.01))

        # State change -> new, higher sequence.
        provider.bump()
        second = await manager._tick(now=0.02)
        self.assertEqual(second["type"], "state")
        self.assertEqual(second["sequence"], 2)

        # Idle past heartbeat window -> heartbeat, sequence unchanged.
        beat = await manager._tick(now=0.20)
        self.assertEqual(beat["type"], "heartbeat")
        self.assertEqual(beat["sequence"], 2)

    async def test_broadcast_drops_lagging_client(self) -> None:
        manager = ConnectionManager(FakeProvider(), queue_max=1)
        _, q1 = manager.connect()
        slow_id, q2 = manager.connect()
        q2.put_nowait({"filler": True})  # q2 now full

        manager._broadcast({"type": "state", "sequence": 1})

        self.assertEqual(manager.client_count, 1)  # lagging client removed
        self.assertNotIn(slow_id, manager._clients)
        self.assertEqual(q1.get_nowait()["sequence"], 1)  # healthy client served

    async def test_disconnect_reduces_count(self) -> None:
        manager = ConnectionManager(FakeProvider())
        cid, _ = manager.connect()
        self.assertEqual(manager.client_count, 1)
        manager.disconnect(cid)
        self.assertEqual(manager.client_count, 0)

    async def test_start_stop_no_leaked_task(self) -> None:
        manager = ConnectionManager(FakeProvider(), poll_interval=0.01)
        manager.start()
        task = manager._broadcaster
        self.assertIsNotNone(task)
        await asyncio.sleep(0.03)  # let it run a few ticks
        await manager.stop()
        self.assertIsNone(manager._broadcaster)
        self.assertTrue(task.done())  # cancelled cleanly, no leak


SCHEMA_KEYS = {"portfolio", "market", "strategies", "trades", "equity_curve", "control"}


class WsEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original = dash.provider
        dash.provider = MockDashboardProvider(seed=7, interval=3600)

    def tearDown(self) -> None:
        dash.provider.stop()
        dash.provider = self._original

    def test_initial_snapshot_on_connect(self) -> None:
        with TestClient(dash.app) as client:
            with client.websocket_connect("/ws") as ws:
                msg = ws.receive_json()
                self.assertEqual(msg["type"], "state")
                self.assertIsInstance(msg["sequence"], int)
                self.assertIn("sent_at", msg)
                self.assertLessEqual(SCHEMA_KEYS, set(msg["data"]))

    def test_multiple_simultaneous_clients(self) -> None:
        with TestClient(dash.app) as client:
            with client.websocket_connect("/ws") as ws1, client.websocket_connect(
                "/ws"
            ) as ws2:
                self.assertEqual(ws1.receive_json()["type"], "state")
                self.assertEqual(ws2.receive_json()["type"], "state")
                self.assertGreaterEqual(dash.manager.client_count, 2)

    def test_control_change_streams_higher_sequence(self) -> None:
        with TestClient(dash.app) as client:
            with client.websocket_connect("/ws") as ws:
                first = ws.receive_json()
                client.post("/api/control/trading", json={"enabled": False})
                deadline = time.time() + 4
                got_higher = False
                while time.time() < deadline:
                    msg = ws.receive_json()
                    if msg["type"] == "state" and msg["sequence"] > first["sequence"]:
                        got_higher = True
                        self.assertFalse(msg["data"]["control"]["trading_enabled"])
                        break
                self.assertTrue(got_higher)

    def test_disconnect_cleanup(self) -> None:
        with TestClient(dash.app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                self.assertGreaterEqual(dash.manager.client_count, 1)
            deadline = time.time() + 2
            while dash.manager.client_count != 0 and time.time() < deadline:
                time.sleep(0.02)
            self.assertEqual(dash.manager.client_count, 0)


class WsRuntimeProviderTests(unittest.TestCase):
    """The default (runtime) provider must serve the same stream contract."""

    def test_runtime_provider_initial_snapshot(self) -> None:
        with TestClient(dash.app) as client:  # uses default runtime provider
            with client.websocket_connect("/ws") as ws:
                msg = ws.receive_json()
                self.assertEqual(msg["type"], "state")
                self.assertLessEqual(SCHEMA_KEYS, set(msg["data"]))
                self.assertEqual(msg["data"]["mode"], "UI-4 runtime")


if __name__ == "__main__":
    unittest.main()

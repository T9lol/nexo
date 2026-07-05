"""Real-time WebSocket streaming for the dashboard (UI-5).

A single broadcaster task samples the provider snapshot on a bounded cadence
and fans it out to connected clients. It is strictly read-only over domain
state (the provider's own lock keeps snapshots consistent) and never holds a
second mutable copy of runtime state.

Transport envelope::

    {"type": "state", "sequence": N, "sent_at": "ISO-8601", "data": {<snapshot>}}
    {"type": "heartbeat", "sequence": N, "sent_at": "ISO-8601"}

Sequence numbers increase monotonically for one server process so the frontend
can discard stale/out-of-order messages.
"""

from __future__ import annotations

import asyncio
import contextlib
import itertools
import json
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

# Bounded cadence: sample at ~300ms, heartbeat when idle, drop clients that lag.
POLL_INTERVAL = 0.3
HEARTBEAT_INTERVAL = 5.0
CLIENT_QUEUE_MAX = 32
SEND_TIMEOUT = 5.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _signature(data: dict[str, Any]) -> str:
    """Stable change signature that ignores the volatile timestamp so we do not
    broadcast identical snapshots every poll."""
    payload = {key: value for key, value in data.items() if key != "updated_at"}
    return json.dumps(payload, sort_keys=True, default=str)


class ConnectionManager:
    """Owns client queues and the broadcaster task. One instance per app."""

    def __init__(
        self,
        provider: Any,
        poll_interval: float = POLL_INTERVAL,
        heartbeat_interval: float = HEARTBEAT_INTERVAL,
        queue_max: int = CLIENT_QUEUE_MAX,
    ) -> None:
        self.provider = provider
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.queue_max = queue_max
        self._clients: dict[int, asyncio.Queue] = {}
        self._ids = itertools.count(1)
        self._sequence = 0
        self._last_signature: str | None = None
        self._last_sent = 0.0
        self._broadcaster: asyncio.Task | None = None

    # -- registration -------------------------------------------------------

    def connect(self) -> tuple[int, asyncio.Queue]:
        client_id = next(self._ids)
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.queue_max)
        self._clients[client_id] = queue
        return client_id, queue

    def disconnect(self, client_id: int) -> None:
        self._clients.pop(client_id, None)

    @property
    def client_count(self) -> int:
        return len(self._clients)

    def state_envelope(self) -> dict[str, Any]:
        """Current snapshot wrapped for an initial send (no sequence bump)."""
        return {
            "type": "state",
            "sequence": self._sequence,
            "sent_at": _now_iso(),
            "data": self.provider.snapshot(),
        }

    # -- broadcasting -------------------------------------------------------

    def _broadcast(self, message: dict[str, Any]) -> None:
        lagging: list[int] = []
        for client_id, queue in self._clients.items():
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                lagging.append(client_id)  # one slow client never blocks others
        for client_id in lagging:
            queue = self._clients.pop(client_id, None)
            if queue is not None:
                with contextlib.suppress(asyncio.QueueFull):
                    queue.put_nowait(None)  # sentinel -> sender stops, ws closes

    async def _tick(self, now: float | None = None) -> dict[str, Any] | None:
        """One sample: broadcast on change, else heartbeat when idle."""
        if now is None:
            now = time.monotonic()
        data = self.provider.snapshot()
        signature = _signature(data)
        if signature != self._last_signature:
            self._last_signature = signature
            self._sequence += 1
            self._last_sent = now
            message = {
                "type": "state",
                "sequence": self._sequence,
                "sent_at": _now_iso(),
                "data": data,
            }
            self._broadcast(message)
            return message
        if now - self._last_sent >= self.heartbeat_interval:
            self._last_sent = now
            message = {
                "type": "heartbeat",
                "sequence": self._sequence,
                "sent_at": _now_iso(),
            }
            self._broadcast(message)
            return message
        return None

    async def _run(self) -> None:
        while True:
            await asyncio.sleep(self.poll_interval)
            self._last_sent = self._last_sent or time.monotonic()
            await self._tick()

    def start(self) -> None:
        if self._broadcaster is None:
            self._last_sent = time.monotonic()
            self._broadcaster = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._broadcaster is not None:
            self._broadcaster.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._broadcaster
            self._broadcaster = None
        for queue in list(self._clients.values()):
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(None)  # release senders so connections close
        self._clients.clear()


async def stream(websocket: WebSocket, manager: ConnectionManager) -> None:
    """Serve one WebSocket client: initial snapshot, then queued broadcasts."""
    await websocket.accept()
    client_id, queue = manager.connect()
    try:
        await websocket.send_json(manager.state_envelope())
    except Exception:
        manager.disconnect(client_id)
        return

    async def sender() -> None:
        while True:
            message = await queue.get()
            if message is None:  # shutdown / dropped sentinel
                break
            await asyncio.wait_for(
                websocket.send_json(message), timeout=SEND_TIMEOUT
            )

    async def receiver() -> None:
        # We do not expect client messages; this detects disconnects.
        while True:
            await websocket.receive_text()

    send_task = asyncio.create_task(sender())
    recv_task = asyncio.create_task(receiver())
    try:
        await asyncio.wait(
            {send_task, recv_task}, return_when=asyncio.FIRST_COMPLETED
        )
    except WebSocketDisconnect:
        pass
    finally:
        for task in (send_task, recv_task):
            task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await asyncio.gather(send_task, recv_task, return_exceptions=True)
        manager.disconnect(client_id)
        with contextlib.suppress(Exception):
            await websocket.close()

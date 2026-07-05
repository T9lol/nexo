"""Synchronous in-process event bus."""

from collections import defaultdict
from collections.abc import Callable
from typing import Any


Event = dict[str, Any]
EventHandler = Callable[[Event], None]


class EventBus:
    """Publish an event to every handler subscribed to its event type."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, data: Event) -> None:
        # Copy the list so handlers may safely subscribe during publication.
        for handler in list(self._subscribers.get(event_type, [])):
            handler(data)

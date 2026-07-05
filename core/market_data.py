"""Simulated live market-data source."""

import random
import threading

from core.event_bus import EventBus


class MarketDataFeed:
    def __init__(
        self,
        event_bus: EventBus,
        start_price: float = 100.0,
        interval_seconds: float = 1.0,
        seed: int | None = None,
    ) -> None:
        if start_price <= 0:
            raise ValueError("start_price must be positive")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.event_bus = event_bus
        self.price = start_price
        self.interval_seconds = interval_seconds
        self._random = random.Random(seed)

    def start(self, stop_event: threading.Event) -> None:
        """Publish simulated BTC prices until stop_event is set."""
        while not stop_event.is_set():
            self.price += self._random.uniform(-1, 1)
            self.event_bus.publish(
                "MARKET_PRICE",
                {"symbol": "BTC", "price": round(self.price, 2)},
            )
            stop_event.wait(self.interval_seconds)

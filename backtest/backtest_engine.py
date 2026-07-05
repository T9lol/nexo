"""Historical market replay."""

from collections.abc import Iterable

from core.event_bus import EventBus


class BacktestEngine:
    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.history: list[float] = []

    def load_data(self, prices: Iterable[float]) -> None:
        history = [float(price) for price in prices]
        if not history:
            raise ValueError("Backtest history cannot be empty")
        if any(price <= 0 for price in history):
            raise ValueError("Every historical price must be positive")
        self.history = history

    def run(self) -> float:
        if not self.history:
            raise RuntimeError("Load historical data before running a backtest")
        print("\n===== BACKTEST START =====\n", flush=True)
        for price in self.history:
            self.event_bus.publish(
                "MARKET_PRICE", {"symbol": "BTC", "price": price}
            )
        print("\n===== BACKTEST END =====\n", flush=True)
        return self.history[-1]

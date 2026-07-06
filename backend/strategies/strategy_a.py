"""Baseline threshold strategy."""

from core.event_bus import Event, EventBus
from strategies.base import BaseStrategy


class StrategyA(BaseStrategy):
    """Buy one BTC below 100 and sell one above 101."""

    name = "A"

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(event_bus)

    def on_price(self, event: Event) -> None:
        price = float(event["price"])
        symbol = str(event["symbol"])
        if price < 100:
            self.publish_signal("BUY", symbol, price, 1.0)
        elif price > 101:
            self.publish_signal("SELL", symbol, price, 1.0)

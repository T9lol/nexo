"""Selective threshold strategy."""

from core.event_bus import Event, EventBus
from strategies.base import BaseStrategy


class StrategyB(BaseStrategy):
    """Trade two BTC only when price crosses wider thresholds."""

    name = "B"

    def __init__(self, event_bus: EventBus) -> None:
        super().__init__(event_bus)

    def on_price(self, event: Event) -> None:
        price = float(event["price"])
        symbol = str(event["symbol"])
        if price < 98:
            self.publish_signal("BUY", symbol, price, 2.0)
        elif price > 103:
            self.publish_signal("SELL", symbol, price, 2.0)

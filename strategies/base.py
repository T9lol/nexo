"""Shared strategy interface."""

from abc import ABC, abstractmethod

from core.event_bus import Event, EventBus


class BaseStrategy(ABC):
    """A strategy may emit signals but must never mutate portfolio state."""

    name = "base"

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    @abstractmethod
    def on_price(self, event: Event) -> None:
        """React to one market-price event."""

    def publish_signal(
        self,
        action: str,
        symbol: str,
        price: float,
        amount: float,
    ) -> None:
        self.event_bus.publish(
            "SIGNAL",
            {
                "strategy": self.name,
                "action": action,
                "symbol": symbol,
                "price": price,
                "amount": amount,
            },
        )

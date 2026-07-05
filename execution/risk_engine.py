"""Pre-trade portfolio risk rules."""

from core.event_bus import Event
from state.portfolio import Portfolio


class RiskEngine:
    def __init__(self, max_position: float = 5.0) -> None:
        if max_position <= 0:
            raise ValueError("max_position must be positive")
        self.max_position = max_position
        self.last_error: str | None = None

    def check(self, signal: Event, portfolio: Portfolio) -> bool:
        action = str(signal["action"]).upper()
        amount = float(signal["amount"])
        self.last_error = None

        if amount <= 0:
            self.last_error = "ORDER blocked - invalid amount"
        elif action == "BUY" and portfolio.asset + amount > self.max_position:
            self.last_error = (
                f"BUY blocked - position limit reached ({self.max_position:g} BTC)"
            )
        elif action == "SELL" and portfolio.asset < amount:
            self.last_error = "SELL blocked - not enough asset"
        elif action not in {"BUY", "SELL"}:
            self.last_error = f"ORDER blocked - unknown action: {action}"

        return self.last_error is None

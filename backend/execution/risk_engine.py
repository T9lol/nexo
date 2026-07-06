"""Pre-trade portfolio risk rules."""

from core.event_bus import Event
from state.portfolio import Portfolio


class RiskEngine:
    def __init__(
        self, max_position: float = 5.0, position_limit_enabled: bool = True
    ) -> None:
        if max_position <= 0:
            raise ValueError("max_position must be positive")
        self.max_position = max_position
        # The position-limit is the only *configurable* policy. The remaining
        # checks below (valid amount, valid action, no short beyond holdings)
        # are mandatory invariants and cannot be disabled from the UI.
        self.position_limit_enabled = position_limit_enabled
        self.last_error: str | None = None

    def check(self, signal: Event, portfolio: Portfolio) -> bool:
        action = str(signal["action"]).upper()
        amount = float(signal["amount"])
        self.last_error = None

        if amount <= 0:
            self.last_error = "ORDER blocked - invalid amount"
        elif action not in {"BUY", "SELL"}:
            self.last_error = f"ORDER blocked - unknown action: {action}"
        elif (
            action == "BUY"
            and self.position_limit_enabled
            and portfolio.asset + amount > self.max_position
        ):
            self.last_error = (
                f"BUY blocked - position limit reached ({self.max_position:g} BTC)"
            )
        elif action == "SELL" and portfolio.asset < amount:
            self.last_error = "SELL blocked - not enough asset"

        return self.last_error is None

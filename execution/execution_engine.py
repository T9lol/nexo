"""Simulated order execution."""

from core.event_bus import Event
from execution.risk_engine import RiskEngine
from observability.alert import AlertSystem
from observability.logger import Logger
from state.analytics import Analytics
from state.portfolio import Portfolio


class ExecutionEngine:
    """Apply risk-approved trading signals to portfolio state."""

    def __init__(
        self,
        portfolio: Portfolio,
        risk_engine: RiskEngine,
        logger: Logger,
        alert: AlertSystem,
        analytics: Analytics,
    ) -> None:
        self.portfolio = portfolio
        self.risk_engine = risk_engine
        self.logger = logger
        self.alert = alert
        self.analytics = analytics

    def on_signal(self, signal: Event) -> None:
        if not self.risk_engine.check(signal, self.portfolio):
            reason = self.risk_engine.last_error or "Trade blocked by risk engine"
            self.logger.risk(reason)
            self.alert.send("Trade blocked by risk engine")
            return

        action = str(signal["action"]).upper()
        symbol = str(signal["symbol"])
        price = float(signal["price"])
        amount = float(signal["amount"])
        strategy = str(signal.get("strategy", "unknown"))

        if price <= 0:
            self._reject(f"{action} blocked - invalid price")
            return

        if action == "BUY":
            cost = price * amount
            if self.portfolio.cash < cost:
                self._reject("BUY blocked - insufficient cash")
                return
            self.portfolio.cash -= cost
            self.portfolio.asset += amount
        else:
            self.portfolio.asset -= amount
            self.portfolio.cash += price * amount

        self.logger.trade(action, symbol, price, amount, strategy)
        self.analytics.record_trade(action, price, amount, strategy)

    def _reject(self, message: str) -> None:
        self.logger.risk(message)
        self.alert.send(message)

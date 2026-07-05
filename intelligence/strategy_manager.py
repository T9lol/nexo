"""Adaptive multi-strategy orchestration."""

from typing import Protocol

from core.event_bus import Event
from intelligence.evaluator import StrategyEvaluator
from state.portfolio import Portfolio


class PriceStrategy(Protocol):
    def on_price(self, event: Event) -> None: ...


class StrategyManager:
    def __init__(
        self,
        strategies: dict[str, PriceStrategy],
        evaluator: StrategyEvaluator,
    ) -> None:
        if not strategies:
            raise ValueError("At least one strategy is required")
        self.strategies = strategies
        self.evaluator = evaluator
        self.last_selected: str | None = None
        self.last_equity: float | None = None

    def on_price(self, event: Event) -> None:
        """Route a live price only to the adaptive winner."""
        self.last_selected = self.select_best()
        if self.last_selected is not None:
            self.strategies[self.last_selected].on_price(event)

    def on_price_all(self, event: Event) -> None:
        """Run every strategy in explicit research mode."""
        self.last_selected = None
        for strategy in self.strategies.values():
            strategy.on_price(event)

    def observe_reward(self, event: Event, portfolio: Portfolio) -> None:
        price = float(event["price"])
        equity = portfolio.total_value(price)
        if self.last_equity is not None and self.last_selected is not None:
            self.evaluator.update(self.last_selected, equity - self.last_equity)
        self.last_equity = equity

    def record_result(self, name: str, pnl: float) -> None:
        if name not in self.strategies:
            raise KeyError(f"Unknown strategy: {name}")
        self.evaluator.update(name, pnl)

    def select_best(self) -> str | None:
        best = self.evaluator.weighted_best()
        if best is not None and best not in self.strategies:
            raise KeyError(f"Evaluator selected unknown strategy: {best}")
        return best

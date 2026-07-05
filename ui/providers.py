"""Dashboard provider interface plus the mock and real-runtime providers.

The dashboard renders a single ``/api/state`` schema. A *provider* supplies
that schema. UI-1 shipped a deterministic mock; UI-2 adds a provider driven by
the real NeXo runtime (EventBus, StrategyManager, ExecutionEngine, Portfolio,
Analytics, MarketDataFeed).

Both providers are strictly read-only over domain state:

* Strategies only publish signals; they never mutate the portfolio.
* Risk checks run (inside ExecutionEngine) before any state mutation.
* This UI layer only *observes* Portfolio, Analytics, and the evaluator - it
  never writes portfolio positions, risk config, or strategy weights.

The strategy selector is a heuristic reward-weighted evaluator, not a trained
ML/RL model.
"""

from __future__ import annotations

import os
import random
import threading
from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timezone
from io import StringIO
from threading import Lock
from typing import Any, Protocol, runtime_checkable

from backtest import BacktestEngine, PRICE_HISTORY
from core import EventBus, MarketDataFeed
from execution import ExecutionEngine, RiskEngine
from intelligence import StrategyEvaluator, StrategyManager
from observability import AlertSystem, Logger
from state import Analytics, Portfolio
from strategies import BaseStrategy, StrategyA, StrategyB


def utc_time() -> str:
    return datetime.now(timezone.utc).isoformat()


@runtime_checkable
class DashboardProvider(Protocol):
    """A source of dashboard state in the shared ``/api/state`` schema."""

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable state snapshot (deep-copied)."""

    def start(self) -> None:
        """Begin producing live updates (idempotent)."""

    def stop(self) -> None:
        """Stop producing updates and release resources (idempotent)."""


# ---------------------------------------------------------------------------
# UI-1 deterministic mock
# ---------------------------------------------------------------------------


class DashboardStore:
    """Thread-safe mock state behind the UI-1 dashboard.

    Deterministic given a seed; kept as a demo fallback for UI-2.
    """

    def __init__(self, seed: int = 42) -> None:
        self._lock = Lock()
        self._random = random.Random(seed)
        self.cash = 10_000.0
        self.asset = 0.0
        self.price = 100.0
        self.initial_equity = 10_000.0
        self.previous_equity = self.initial_equity
        self.tick_count = 0
        self.selected_strategy = "A"
        self.strategies: dict[str, dict[str, float | int]] = {
            "A": {"score": 30.0, "weight": 1.05, "updates": 1},
            "B": {"score": 24.0, "weight": 1.05, "updates": 1},
        }
        self.trades: list[dict[str, Any]] = []
        self.equity_curve: list[dict[str, Any]] = [
            {"time": utc_time(), "value": self.initial_equity}
        ]

    def tick(self) -> None:
        with self._lock:
            self.tick_count += 1
            self.price = round(max(1.0, self.price + self._random.uniform(-0.8, 0.8)), 2)

            if self.price < 99.55 and self.asset < 3:
                self._execute("BUY", 1.0)
            elif self.price > 100.65 and self.asset >= 1:
                self._execute("SELL", 1.0)

            equity = round(self.cash + self.asset * self.price, 2)
            reward = equity - self.previous_equity
            strategy = self.strategies[self.selected_strategy]
            strategy["score"] = round(float(strategy["score"]) + reward, 2)
            strategy["updates"] = int(strategy["updates"]) + 1
            if reward > 0:
                strategy["weight"] = min(10.0, float(strategy["weight"]) * 1.01)
            elif reward < 0:
                strategy["weight"] = max(0.1, float(strategy["weight"]) * 0.99)

            self.selected_strategy = max(
                self.strategies,
                key=lambda name: float(self.strategies[name]["score"])
                * float(self.strategies[name]["weight"]),
            )
            self.previous_equity = equity
            self.equity_curve.append({"time": utc_time(), "value": equity})
            self.equity_curve = self.equity_curve[-120:]

    def _execute(self, action: str, amount: float) -> None:
        if action == "BUY":
            cost = self.price * amount
            if self.cash < cost:
                return
            self.cash -= cost
            self.asset += amount
        else:
            self.cash += self.price * amount
            self.asset -= amount

        self.trades.insert(
            0,
            {
                "id": f"trade-{self.tick_count}",
                "time": utc_time(),
                "strategy": self.selected_strategy,
                "action": action,
                "symbol": "BTC",
                "price": self.price,
                "amount": amount,
            },
        )
        self.trades = self.trades[:30]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            equity = round(self.cash + self.asset * self.price, 2)
            return deepcopy(
                {
                    "status": "live",
                    "mode": "UI-1 simulation",
                    "updated_at": utc_time(),
                    "market": {"symbol": "BTC", "price": self.price},
                    "portfolio": {
                        "cash": round(self.cash, 2),
                        "asset": self.asset,
                        "equity": equity,
                        "pnl": round(equity - self.initial_equity, 2),
                    },
                    "selected_strategy": self.selected_strategy,
                    "strategies": self.strategies,
                    "trades": self.trades,
                    "equity_curve": self.equity_curve,
                }
            )


class MockDashboardProvider:
    """Deterministic demo provider wrapping :class:`DashboardStore`."""

    def __init__(self, seed: int = 42, interval: float = 1.0) -> None:
        self.store = DashboardStore(seed=seed)
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict[str, Any]:
        return self.store.snapshot()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="mock-provider", daemon=True
        )
        self._thread.start()

    def _loop(self) -> None:
        while not self._stop.is_set():
            self.store.tick()
            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None


# ---------------------------------------------------------------------------
# UI-2 real-runtime provider
# ---------------------------------------------------------------------------


class RuntimeDashboardProvider:
    """Read-only adapter over the real NeXo runtime.

    Wires the same components ``main.build_runtime`` uses, runs a
    :class:`MarketDataFeed` in a background thread, and observes the resulting
    state. It publishes real portfolio, equity history, executed trades, the
    selected strategy, and evaluator scores/weights through the existing
    ``/api/state`` schema.

    The whole ``MARKET_PRICE`` cascade runs under one lock so snapshots are
    internally consistent with concurrent HTTP reads.
    """

    def __init__(
        self,
        interval: float = 1.0,
        seed: int | None = None,
        max_points: int = 120,
        max_trades: int = 30,
        seed_evaluator: bool = True,
    ) -> None:
        self.max_points = max_points
        self.max_trades = max_trades
        self._lock = Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        self.bus = EventBus()
        self.portfolio = Portfolio(quiet=True)
        self.analytics = Analytics(initial_capital=self.portfolio.cash)
        self.evaluator = StrategyEvaluator()
        self.logger = Logger(quiet=True)
        self.manager = StrategyManager(
            {"A": StrategyA(self.bus), "B": StrategyB(self.bus)}, self.evaluator
        )
        self.execution = ExecutionEngine(
            self.portfolio,
            RiskEngine(max_position=5),
            self.logger,
            AlertSystem(quiet=True),
            self.analytics,
        )
        # Strategy -> SIGNAL -> risk -> execution boundary preserved via the bus.
        self.bus.subscribe("SIGNAL", self.execution.on_signal)

        self.market = MarketDataFeed(
            self.bus, interval_seconds=interval, seed=seed
        )

        # Observer-only view state.
        self._last_symbol = "BTC"
        self._trade_seq = 0
        self._recorded = 0
        self._trades: list[dict[str, Any]] = []
        self._equity_curve: list[dict[str, Any]] = [
            {"time": utc_time(), "value": round(self.portfolio.cash, 2)}
        ]

        # The market feed is the only MARKET_PRICE publisher; a single locked
        # handler drives the domain cascade and then records the observed state.
        self.bus.subscribe("MARKET_PRICE", self._on_market_price)

        if seed_evaluator:
            self._seed_evaluator()

    # -- runtime wiring -----------------------------------------------------

    def _seed_evaluator(self) -> None:
        """Prime the evaluator with an isolated per-strategy backtest score.

        Mirrors ``main.seed_evaluator`` but stays silent and never touches the
        live portfolio (each candidate runs in its own throwaway account).
        """
        candidates: tuple[tuple[str, type[BaseStrategy]], ...] = (
            ("A", StrategyA),
            ("B", StrategyB),
        )
        with redirect_stdout(StringIO()):
            for name, strategy_type in candidates:
                pnl = self._evaluate_isolated(strategy_type)
                self.evaluator.update(name, pnl)

    @staticmethod
    def _evaluate_isolated(strategy_type: type[BaseStrategy]) -> float:
        bus = EventBus()
        portfolio = Portfolio(quiet=True)
        analytics = Analytics(initial_capital=portfolio.cash)
        strategy = strategy_type(bus)
        execution = ExecutionEngine(
            portfolio,
            RiskEngine(max_position=5),
            Logger(quiet=True),
            AlertSystem(quiet=True),
            analytics,
        )
        bus.subscribe("MARKET_PRICE", strategy.on_price)
        bus.subscribe("SIGNAL", execution.on_signal)
        bus.subscribe("MARKET_PRICE", portfolio.on_market_price)
        backtest = BacktestEngine(bus)
        backtest.load_data(PRICE_HISTORY)
        final_price = backtest.run()
        return analytics.pnl(portfolio, final_price)

    def _on_market_price(self, event: dict[str, Any]) -> None:
        with self._lock:
            # Route to the adaptive winner -> SIGNAL -> risk -> execution.
            self.manager.on_price(event)
            # Update valuation and adaptive reward from post-trade state.
            self.portfolio.on_market_price(event)
            self.manager.observe_reward(event, self.portfolio)
            self._record(event)

    def _record(self, event: dict[str, Any]) -> None:
        price = float(event["price"])
        self._last_symbol = str(event["symbol"])

        equity = round(self.portfolio.total_value(price), 2)
        self._equity_curve.append({"time": utc_time(), "value": equity})
        self._equity_curve = self._equity_curve[-self.max_points :]

        # Enrich trades the runtime recorded but the UI schema needs more of.
        for trade in self.analytics.trades[self._recorded :]:
            self._trade_seq += 1
            self._trades.insert(
                0,
                {
                    "id": f"trade-{self._trade_seq}",
                    "time": utc_time(),
                    "strategy": str(trade.get("strategy", "unknown")),
                    "action": str(trade["action"]),
                    "symbol": self._last_symbol,
                    "price": float(trade["price"]),
                    "amount": float(trade["amount"]),
                },
            )
        self._recorded = len(self.analytics.trades)
        self._trades = self._trades[: self.max_trades]

    # -- driving ------------------------------------------------------------

    def tick_once(self) -> float:
        """Advance the market by one price (test/manual driver)."""
        return self.market.step()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self.market.start,
            args=(self._stop,),
            name="runtime-market",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    # -- snapshot -----------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            price = (
                self.portfolio.last_price
                if self.portfolio.last_price is not None
                else self.market.price
            )
            strategies = {
                name: {
                    "score": round(self.evaluator.scores.get(name, 0.0), 2),
                    "weight": round(self.evaluator.weights.get(name, 1.0), 4),
                    "updates": int(self.evaluator.updates.get(name, 0)),
                }
                for name in self.manager.strategies
            }
            selected = self.manager.select_best() or next(
                iter(self.manager.strategies)
            )
            return deepcopy(
                {
                    "status": "live",
                    "mode": "UI-2 runtime",
                    "updated_at": utc_time(),
                    "market": {
                        "symbol": self._last_symbol,
                        "price": round(price, 2),
                    },
                    "portfolio": {
                        "cash": round(self.portfolio.cash, 2),
                        "asset": self.portfolio.asset,
                        "equity": round(self.portfolio.total_value(price), 2),
                        "pnl": round(self.analytics.pnl(self.portfolio, price), 2),
                    },
                    "selected_strategy": selected,
                    "strategies": strategies,
                    "trades": self._trades,
                    "equity_curve": self._equity_curve,
                }
            )


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------


def build_provider(name: str | None = None) -> DashboardProvider:
    """Build a provider. Defaults to the real runtime; ``mock`` opts into the
    deterministic UI-1 demo (via ``NEXO_DASHBOARD_PROVIDER`` or ``name``)."""
    choice = (name or os.environ.get("NEXO_DASHBOARD_PROVIDER") or "runtime").lower()
    if choice == "mock":
        return MockDashboardProvider()
    if choice == "runtime":
        return RuntimeDashboardProvider()
    raise ValueError(
        f"Unknown dashboard provider: {choice!r} (expected 'runtime' or 'mock')"
    )

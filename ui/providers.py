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
from dataclasses import dataclass
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


# ---------------------------------------------------------------------------
# Control state (shared UI-4 control contract)
# ---------------------------------------------------------------------------

STRATEGY_POLICIES = ("auto", "A", "B")
RUNTIME_MODES = ("live", "backtest")
MAX_POSITION = 5.0


@dataclass
class ControlState:
    """The user-configurable control surface. Read-only invariants (valid
    price/amount, no negative cash, no short inventory) live in the domain and
    are *not* represented here because they can never be toggled off."""

    trading_enabled: bool = True
    strategy_policy: str = "auto"  # auto | A | B
    position_limit_enabled: bool = True
    mode: str = "live"  # live | backtest


def control_dict(
    control: ControlState, effective_strategy: str | None
) -> dict[str, Any]:
    """Canonical, JSON-safe control state exposed to the frontend."""
    return {
        "trading_enabled": control.trading_enabled,
        "strategy_policy": control.strategy_policy,
        # Resolved routing target: evaluator-best under "auto", else the manual pick.
        "effective_strategy": effective_strategy,
        "manual_override": control.strategy_policy in ("A", "B"),
        "position_limit_enabled": control.position_limit_enabled,
        "mode": control.mode,
        "environment": "local-simulation",
        "allowed": {
            "strategy_policy": list(STRATEGY_POLICIES),
            "mode": list(RUNTIME_MODES),
        },
    }


# ---------------------------------------------------------------------------
# Deterministic, isolated backtest (shared by both providers)
# ---------------------------------------------------------------------------


def _evaluate_isolated(strategy_type: type[BaseStrategy]) -> float:
    """Score one strategy in a throwaway account over the fixed history."""
    bus = EventBus()
    portfolio = Portfolio(quiet=True)
    analytics = Analytics(initial_capital=portfolio.cash)
    strategy = strategy_type(bus)
    execution = ExecutionEngine(
        portfolio,
        RiskEngine(max_position=MAX_POSITION),
        Logger(quiet=True),
        AlertSystem(quiet=True),
        analytics,
    )
    bus.subscribe("MARKET_PRICE", strategy.on_price)
    bus.subscribe("SIGNAL", execution.on_signal)
    bus.subscribe("MARKET_PRICE", portfolio.on_market_price)
    backtest = BacktestEngine(bus)
    backtest.load_data(PRICE_HISTORY)
    with redirect_stdout(StringIO()):
        final_price = backtest.run()
    return analytics.pnl(portfolio, final_price)


def _seed_evaluator(evaluator: StrategyEvaluator) -> None:
    """Prime an evaluator with each strategy's isolated backtest pnl."""
    for name, strategy_type in (("A", StrategyA), ("B", StrategyB)):
        evaluator.update(name, _evaluate_isolated(strategy_type))


def run_reference_backtest(
    policy: str = "auto",
    position_limit_enabled: bool = True,
    max_points: int = 120,
    max_trades: int = 30,
) -> dict[str, Any]:
    """Replay the fixed PRICE_HISTORY through a fully isolated runtime and
    return a snapshot dict (mode ``backtest review``). Deterministic: no RNG,
    its own Portfolio/Analytics/Evaluator, so it cannot touch live state."""
    bus = EventBus()
    portfolio = Portfolio(quiet=True)
    analytics = Analytics(initial_capital=portfolio.cash)
    evaluator = StrategyEvaluator()
    manager = StrategyManager(
        {"A": StrategyA(bus), "B": StrategyB(bus)}, evaluator
    )
    manager.policy = policy if policy in STRATEGY_POLICIES else "auto"
    risk = RiskEngine(
        max_position=MAX_POSITION, position_limit_enabled=position_limit_enabled
    )
    execution = ExecutionEngine(
        portfolio, risk, Logger(quiet=True), AlertSystem(quiet=True), analytics
    )
    _seed_evaluator(evaluator)

    equity_curve: list[dict[str, Any]] = [
        {"time": utc_time(), "value": round(portfolio.cash, 2)}
    ]
    trades: list[dict[str, Any]] = []
    cursor = {"seq": 0, "recorded": 0, "symbol": "BTC"}

    def observe(event: dict[str, Any]) -> None:
        manager.on_price(event)
        portfolio.on_market_price(event)
        manager.observe_reward(event, portfolio)
        price = float(event["price"])
        cursor["symbol"] = str(event["symbol"])
        equity_curve.append(
            {"time": utc_time(), "value": round(portfolio.total_value(price), 2)}
        )
        for trade in analytics.trades[cursor["recorded"] :]:
            cursor["seq"] += 1
            trades.insert(
                0,
                {
                    "id": f"bt-{cursor['seq']}",
                    "time": utc_time(),
                    "strategy": str(trade.get("strategy", "unknown")),
                    "action": str(trade["action"]),
                    "symbol": cursor["symbol"],
                    "price": float(trade["price"]),
                    "amount": float(trade["amount"]),
                },
            )
        cursor["recorded"] = len(analytics.trades)

    bus.subscribe("SIGNAL", execution.on_signal)
    bus.subscribe("MARKET_PRICE", observe)
    engine = BacktestEngine(bus)
    engine.load_data(PRICE_HISTORY)
    with redirect_stdout(StringIO()):
        final_price = engine.run()

    strategies = {
        name: {
            "score": round(evaluator.scores.get(name, 0.0), 2),
            "weight": round(evaluator.weights.get(name, 1.0), 4),
            "updates": int(evaluator.updates.get(name, 0)),
            "adaptive": (
                round(evaluator.weighted_score(name), 2)
                if name in evaluator.scores
                else 0.0
            ),
        }
        for name in manager.strategies
    }
    selected = manager.active_selection() or next(iter(manager.strategies))
    return {
        "status": "live",
        "mode": "backtest review",
        "updated_at": utc_time(),
        "market": {"symbol": cursor["symbol"], "price": round(final_price, 2)},
        "portfolio": {
            "cash": round(portfolio.cash, 2),
            "asset": portfolio.asset,
            "equity": round(portfolio.total_value(final_price), 2),
            "pnl": round(analytics.pnl(portfolio, final_price), 2),
        },
        "selected_strategy": selected,
        "strategies": strategies,
        "trades": trades[:max_trades],
        "equity_curve": equity_curve[-max_points:],
    }


@runtime_checkable
class DashboardProvider(Protocol):
    """A source of dashboard state in the shared ``/api/state`` schema."""

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable state snapshot (deep-copied)."""

    def start(self) -> None:
        """Begin producing live updates (idempotent)."""

    def stop(self) -> None:
        """Stop producing updates and release resources (idempotent)."""

    # -- UI-4 control contract (implemented identically by every provider) --

    def get_control(self) -> dict[str, Any]:
        """Return the canonical control state and allowed values."""

    def set_trading(self, enabled: bool) -> dict[str, Any]:
        """Pause/resume executions; return the resulting control state."""

    def set_strategy(self, policy: str) -> dict[str, Any]:
        """Set routing policy (auto|A|B); return the resulting control state."""

    def set_risk(self, position_limit_enabled: bool) -> dict[str, Any]:
        """Toggle the position-limit policy; return the control state."""

    def set_mode(self, mode: str) -> dict[str, Any]:
        """Switch live|backtest with lifecycle isolation; return control state."""


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
        # Control state (mirrors the runtime provider's contract deterministically).
        self.trading_enabled = True
        self.strategy_policy = "auto"
        self.position_limit_enabled = True
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

            # Trading pause blocks executions; market/equity keep moving. The
            # position-limit cap (asset < 3) is skipped when the policy is off,
            # but the cash and inventory invariants inside _execute always hold.
            if self.trading_enabled:
                cap = 3.0 if self.position_limit_enabled else float("inf")
                if self.price < 99.55 and self.asset < cap:
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

            # Manual policy forces the selection; "auto" defers to score x weight.
            if self.strategy_policy in self.strategies:
                self.selected_strategy = self.strategy_policy
            else:
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
                    "strategies": {
                        name: {
                            **item,
                            # Adaptive score = the mock's selection metric.
                            "adaptive": round(
                                float(item["score"]) * float(item["weight"]), 2
                            ),
                        }
                        for name, item in self.strategies.items()
                    },
                    "trades": self.trades,
                    "equity_curve": self.equity_curve,
                }
            )


class MockDashboardProvider:
    """Deterministic demo provider wrapping :class:`DashboardStore`.

    Implements the same UI-4 control contract as the runtime provider so the
    frontend can be exercised deterministically.
    """

    def __init__(self, seed: int = 42, interval: float = 1.0) -> None:
        self.store = DashboardStore(seed=seed)
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._control = ControlState()
        self._control_lock = Lock()
        self._backtest: dict[str, Any] | None = None

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        # Live ticks only run in live mode; backtest is a static replay.
        if self._thread is not None or self._control.mode != "live":
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

    # -- snapshot -----------------------------------------------------------

    def _effective_strategy(self) -> str:
        if self._control.strategy_policy in self.store.strategies:
            return self._control.strategy_policy
        return self.store.selected_strategy

    def snapshot(self) -> dict[str, Any]:
        base = (
            deepcopy(self._backtest)
            if self._backtest is not None
            else self.store.snapshot()
        )
        base["control"] = control_dict(self._control, self._effective_strategy())
        return base

    def get_control(self) -> dict[str, Any]:
        return control_dict(self._control, self._effective_strategy())

    # -- control commands ---------------------------------------------------

    def set_trading(self, enabled: bool) -> dict[str, Any]:
        with self._control_lock:
            with self.store._lock:
                self.store.trading_enabled = bool(enabled)
            self._control.trading_enabled = bool(enabled)
            return self.get_control()

    def set_strategy(self, policy: str) -> dict[str, Any]:
        if policy not in STRATEGY_POLICIES:
            raise ValueError(f"Unknown strategy policy: {policy!r}")
        with self._control_lock:
            with self.store._lock:
                self.store.strategy_policy = policy
            self._control.strategy_policy = policy
            return self.get_control()

    def set_risk(self, position_limit_enabled: bool) -> dict[str, Any]:
        with self._control_lock:
            with self.store._lock:
                self.store.position_limit_enabled = bool(position_limit_enabled)
            self._control.position_limit_enabled = bool(position_limit_enabled)
            return self.get_control()

    def set_mode(self, mode: str) -> dict[str, Any]:
        if mode not in RUNTIME_MODES:
            raise ValueError(f"Unknown mode: {mode!r}")
        with self._control_lock:
            if mode == self._control.mode:
                return self.get_control()
            if mode == "backtest":
                self.stop()  # freeze live ticking; store state preserved
                self._backtest = run_reference_backtest(
                    self._control.strategy_policy,
                    self._control.position_limit_enabled,
                )
                self._control.mode = "backtest"
            else:
                self._backtest = None
                self._control.mode = "live"
                self.start()
            return self.get_control()


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
        # A separate lock serializes control commands so we never hold the
        # snapshot lock while join()ing the market thread (that would deadlock,
        # since the thread's handler also acquires the snapshot lock).
        self._control_lock = Lock()
        self._control = ControlState()
        self._backtest: dict[str, Any] | None = None
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
            RiskEngine(max_position=MAX_POSITION),
            self.logger,
            AlertSystem(quiet=True),
            self.analytics,
        )
        # Strategy -> SIGNAL -> risk -> execution boundary preserved via the bus.
        # The controller gate (_on_signal) enforces the trading pause without
        # touching strategies, execution, or portfolio state.
        self.bus.subscribe("SIGNAL", self._on_signal)

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
        """Prime the evaluator with an isolated per-strategy backtest score."""
        _seed_evaluator(self.evaluator)

    def _on_signal(self, signal: dict[str, Any]) -> None:
        """Controller gate: drop signals while trading is paused (no fills),
        otherwise hand off to the real execution engine."""
        if not self._control.trading_enabled:
            return
        self.execution.on_signal(signal)

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

    def _effective_strategy_locked(self) -> str:
        return self.manager.active_selection() or next(
            iter(self.manager.strategies)
        )

    def _live_snapshot_locked(self) -> dict[str, Any]:
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
                # Adaptive score = the evaluator's real selection metric
                # (reward x weight, with the negative-reward rule).
                "adaptive": (
                    round(self.evaluator.weighted_score(name), 2)
                    if name in self.evaluator.scores
                    else 0.0
                ),
            }
            for name in self.manager.strategies
        }
        return {
            "status": "live",
            "mode": "UI-4 runtime",
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
            "selected_strategy": self._effective_strategy_locked(),
            "strategies": strategies,
            "trades": self._trades,
            "equity_curve": self._equity_curve,
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            if self._backtest is not None:
                snap = deepcopy(self._backtest)
            else:
                snap = deepcopy(self._live_snapshot_locked())
            snap["control"] = control_dict(
                self._control, self._effective_strategy_locked()
            )
            return snap

    # -- control commands ---------------------------------------------------

    def get_control(self) -> dict[str, Any]:
        with self._lock:
            return control_dict(self._control, self._effective_strategy_locked())

    def set_trading(self, enabled: bool) -> dict[str, Any]:
        with self._control_lock:
            with self._lock:
                self._control.trading_enabled = bool(enabled)
            return self.get_control()

    def set_strategy(self, policy: str) -> dict[str, Any]:
        if policy not in STRATEGY_POLICIES:
            raise ValueError(f"Unknown strategy policy: {policy!r}")
        with self._control_lock:
            with self._lock:
                self._control.strategy_policy = policy
                self.manager.policy = policy
            return self.get_control()

    def set_risk(self, position_limit_enabled: bool) -> dict[str, Any]:
        with self._control_lock:
            with self._lock:
                self._control.position_limit_enabled = bool(position_limit_enabled)
                self.execution.risk_engine.position_limit_enabled = bool(
                    position_limit_enabled
                )
            return self.get_control()

    def set_mode(self, mode: str) -> dict[str, Any]:
        if mode not in RUNTIME_MODES:
            raise ValueError(f"Unknown mode: {mode!r}")
        with self._control_lock:
            if mode == self._control.mode:
                return self.get_control()
            if mode == "backtest":
                # Stop the live market thread *without* holding self._lock, then
                # replay a fully isolated backtest. Live state is left frozen.
                self.stop()
                session = run_reference_backtest(
                    self._control.strategy_policy,
                    self._control.position_limit_enabled,
                    max_points=self.max_points,
                    max_trades=self.max_trades,
                )
                with self._lock:
                    self._backtest = session
                    self._control.mode = "backtest"
            else:
                with self._lock:
                    self._backtest = None
                    self._control.mode = "live"
                # Resume the preserved live session (start() is idempotent and
                # only ever runs one market thread).
                self.start()
            return self.get_control()


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

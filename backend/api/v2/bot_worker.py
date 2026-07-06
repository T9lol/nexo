"""Backend-only bot execution worker.

Each tick advances a shared, seeded simulated price (the engine's
``MarketDataFeed``), derives a signal from the real engine strategies
(``StrategyA``/``StrategyB``; ``auto`` follows the isolated-backtest winner), and
applies it as a single paper fill to every *active* subscription of that bot —
persisting a ``trades`` row and respecting the user's risk config. No new trading
logic: signals come straight from the engine strategies.
"""

from __future__ import annotations

import threading
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.logging import get_logger
from api.v2.paper_trading import replay_state
from core import EventBus
from core.market_data import MarketDataFeed
from db.models import (
    Bot,
    RiskConfig,
    Subscription,
    SubscriptionStatus,
    Trade,
    TradeSide,
)
from strategies import StrategyA, StrategyB

logger = get_logger("bot_worker")
_START_PRICE = 100.0


class BotWorker:
    def __init__(self, interval: float = 1.0, seed: int | None = 7) -> None:
        self.interval = interval
        self._last_price = _START_PRICE
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        self._bus = EventBus()
        self._captured: list[dict] = []
        self._bus.subscribe("SIGNAL", self._captured.append)
        self._strat_a = StrategyA(self._bus)
        self._strat_b = StrategyB(self._bus)
        self._market = MarketDataFeed(EventBus(), start_price=_START_PRICE, seed=seed)
        self._winner: str | None = None

    # -- signal generation --------------------------------------------------

    def _winner_key(self) -> str:
        if self._winner is None:
            # Reuse the engine's isolated evaluation to pick the adaptive winner.
            from ui.providers import _evaluate_isolated

            score_a = _evaluate_isolated(StrategyA)
            score_b = _evaluate_isolated(StrategyB)
            self._winner = "A" if score_a >= score_b else "B"
        return self._winner

    def _signals(self, price: float) -> dict[str, dict]:
        """Return {"A": signal, "B": signal} for any strategy that fired."""

        self._captured.clear()
        event = {"symbol": "BTC", "price": price}
        self._strat_a.on_price(event)
        self._strat_b.on_price(event)
        return {s["strategy"]: s for s in self._captured}

    def _signal_for(self, bot_key: str | None, by_strategy: dict[str, dict]) -> dict | None:
        if bot_key == "auto":
            return by_strategy.get(self._winner_key())  # backtest only when needed
        return by_strategy.get(bot_key)

    # -- execution ----------------------------------------------------------

    def _risk_for(self, session: Session, user_id: int) -> RiskConfig:
        rc = session.scalar(select(RiskConfig).where(RiskConfig.user_id == user_id))
        if rc is None:
            rc = RiskConfig(user_id=user_id)
            session.add(rc)
            session.flush()
        return rc

    def _apply(self, session: Session, sub: Subscription, signal: dict | None, price: float) -> Trade | None:
        if signal is None:
            return None
        state = replay_state(session, sub.id, sub.capital)
        risk = self._risk_for(session, sub.user_id)
        action = str(signal["action"])
        qty = Decimal(str(signal["amount"]))
        p = Decimal(str(price))

        if action == TradeSide.BUY.value:
            cost = p * qty
            if risk.position_limit_enabled and (state.position + qty) > Decimal(str(risk.max_position)):
                return None
            if state.cash < cost:
                return None
            pnl = Decimal("0")
        elif action == TradeSide.SELL.value:
            if state.position < qty:
                return None
            pnl = (p - state.avg_cost) * qty
        else:
            return None

        trade = Trade(
            subscription_id=sub.id,
            user_id=sub.user_id,
            bot_id=sub.bot_id,
            symbol="BTC",
            side=action,
            quantity=qty,
            price=p,
            value=p * qty,
            pnl=pnl,
            status="filled",
        )
        session.add(trade)
        session.flush()  # so the next subscription/tick replays it
        return trade

    def tick_once(self, session: Session) -> dict[str, object]:
        with self._lock:
            price = self._market.step()
            self._last_price = price
        by_strategy = self._signals(price)

        subs = session.scalars(
            select(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE.value)
        ).all()
        executed = 0
        for sub in subs:
            bot = session.get(Bot, sub.bot_id)
            key = bot.key if bot is not None else None
            signal = self._signal_for(key, by_strategy)
            if self._apply(session, sub, signal, price) is not None:
                executed += 1
        session.commit()
        return {"price": price, "executed": executed}

    def current_price(self) -> float:
        with self._lock:
            return self._last_price

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="bot-worker", daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        from db import SessionLocal

        while not self._stop.is_set():
            try:
                with SessionLocal() as session:
                    self.tick_once(session)
            except Exception:  # noqa: BLE001 - keep the worker alive
                logger.warning("bot worker tick failed", extra={"event": "worker_tick_error"})
            self._stop.wait(self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None


# Module singleton (thread not started until start()).
_worker: BotWorker | None = None


def get_worker() -> BotWorker:
    global _worker
    if _worker is None:
        _worker = BotWorker()
    return _worker


def reset_worker() -> None:
    """Discard the singleton (used by tests for isolation)."""

    global _worker
    if _worker is not None:
        _worker.stop()
    _worker = None


def current_price() -> float:
    return get_worker().current_price()

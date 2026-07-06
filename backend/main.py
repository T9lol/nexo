"""Command-line entry point for NeXo."""

import argparse
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
import threading

from backtest import BacktestEngine, PRICE_HISTORY
from core import EventBus, MarketDataFeed
from execution import ExecutionEngine, RiskEngine
from intelligence import StrategyEvaluator, StrategyManager
from observability import AlertSystem, Logger
from state import Analytics, Portfolio
from strategies import BaseStrategy, StrategyA, StrategyB


@dataclass
class Runtime:
    bus: EventBus
    portfolio: Portfolio
    analytics: Analytics
    evaluator: StrategyEvaluator
    manager: StrategyManager
    logger: Logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NeXo event-driven adaptive trading simulator"
    )
    parser.add_argument(
        "--mode",
        choices=("live", "backtest", "compare"),
        default="live",
        help="Execution mode (default: live)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Stop live mode after N seconds (default: run until Ctrl+C)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between simulated live prices (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible live simulation",
    )
    return parser.parse_args()


def build_runtime() -> Runtime:
    bus = EventBus()
    portfolio = Portfolio()
    analytics = Analytics(initial_capital=portfolio.cash)
    evaluator = StrategyEvaluator()
    logger = Logger()
    manager = StrategyManager(
        {"A": StrategyA(bus), "B": StrategyB(bus)}, evaluator
    )
    execution = ExecutionEngine(
        portfolio,
        RiskEngine(max_position=5),
        logger,
        AlertSystem(),
        analytics,
    )

    bus.subscribe("SIGNAL", execution.on_signal)
    return Runtime(bus, portfolio, analytics, evaluator, manager, logger)


def wire_market_events(runtime: Runtime, research_mode: bool = False) -> None:
    price_handler = (
        runtime.manager.on_price_all
        if research_mode
        else runtime.manager.on_price
    )
    runtime.bus.subscribe("MARKET_PRICE", price_handler)
    runtime.bus.subscribe("MARKET_PRICE", runtime.portfolio.on_market_price)
    # Feedback must run after execution and portfolio valuation.
    runtime.bus.subscribe(
        "MARKET_PRICE",
        lambda event: runtime.manager.observe_reward(event, runtime.portfolio),
    )


def evaluate_strategy(
    name: str,
    strategy_type: type[BaseStrategy],
    history: list[float],
    verbose: bool = True,
) -> float:
    """Evaluate one strategy in an isolated account."""

    def run() -> float:
        print(f"\n##### EVALUATING STRATEGY {name} #####", flush=True)
        bus = EventBus()
        portfolio = Portfolio()
        analytics = Analytics(initial_capital=portfolio.cash)
        strategy = strategy_type(bus)
        execution = ExecutionEngine(
            portfolio,
            RiskEngine(max_position=5),
            Logger(),
            AlertSystem(),
            analytics,
        )
        bus.subscribe("MARKET_PRICE", strategy.on_price)
        bus.subscribe("SIGNAL", execution.on_signal)
        bus.subscribe("MARKET_PRICE", portfolio.on_market_price)

        backtest = BacktestEngine(bus)
        backtest.load_data(history)
        final_price = backtest.run()
        analytics.summary(portfolio, final_price)
        return analytics.pnl(portfolio, final_price)

    if verbose:
        return run()
    with redirect_stdout(StringIO()):
        return run()


def seed_evaluator(runtime: Runtime, verbose: bool = False) -> None:
    candidates: tuple[tuple[str, type[BaseStrategy]], ...] = (
        ("A", StrategyA),
        ("B", StrategyB),
    )
    for name, strategy_type in candidates:
        pnl = evaluate_strategy(name, strategy_type, PRICE_HISTORY, verbose)
        runtime.manager.record_result(name, pnl)


def run_comparison(runtime: Runtime) -> None:
    runtime.logger.log("Strategy comparison is running.")
    seed_evaluator(runtime, verbose=True)
    runtime.evaluator.report()


def run_backtest(runtime: Runtime) -> None:
    runtime.logger.log("Combined-strategy backtest is running.")
    wire_market_events(runtime, research_mode=True)
    backtest = BacktestEngine(runtime.bus)
    backtest.load_data(PRICE_HISTORY)
    final_price = backtest.run()
    runtime.analytics.summary(runtime.portfolio, final_price)


def run_live(runtime: Runtime, args: argparse.Namespace) -> None:
    seed_evaluator(runtime)
    runtime.evaluator.report()
    runtime.logger.log(
        f"Adaptive Intelligence selected Strategy {runtime.manager.select_best()}."
    )
    wire_market_events(runtime)

    stop_event = threading.Event()
    market = MarketDataFeed(
        runtime.bus,
        interval_seconds=args.interval,
        seed=args.seed,
    )
    market_thread = threading.Thread(
        target=market.start,
        args=(stop_event,),
        name="market-data",
        daemon=True,
    )
    runtime.logger.log("Live simulation started. Press Ctrl+C to stop.")
    market_thread.start()

    try:
        if args.duration is None:
            while market_thread.is_alive():
                market_thread.join(timeout=1)
        else:
            stop_event.wait(max(0.0, args.duration))
    except KeyboardInterrupt:
        print("\nStopping NeXo...", flush=True)
    finally:
        stop_event.set()
        market_thread.join(timeout=2)
        if runtime.portfolio.last_price is not None:
            runtime.analytics.summary(
                runtime.portfolio, runtime.portfolio.last_price
            )
            runtime.evaluator.report()


def main() -> None:
    args = parse_args()
    runtime = build_runtime()
    if args.mode == "compare":
        run_comparison(runtime)
    elif args.mode == "backtest":
        run_backtest(runtime)
    else:
        run_live(runtime, args)


if __name__ == "__main__":
    main()

"""Trade history and portfolio performance metrics."""

from typing import Any

from state.portfolio import Portfolio


class Analytics:
    def __init__(self, initial_capital: float = 10_000.0) -> None:
        self.initial_capital = initial_capital
        self.trades: list[dict[str, Any]] = []

    def record_trade(
        self,
        action: str,
        price: float,
        amount: float,
        strategy: str = "unknown",
    ) -> None:
        self.trades.append(
            {
                "action": action,
                "price": price,
                "amount": amount,
                "strategy": strategy,
            }
        )

    def total_value(self, portfolio: Portfolio, current_price: float) -> float:
        return portfolio.total_value(current_price)

    def pnl(self, portfolio: Portfolio, current_price: float) -> float:
        return self.total_value(portfolio, current_price) - self.initial_capital

    def summary(self, portfolio: Portfolio, current_price: float) -> None:
        total = self.total_value(portfolio, current_price)
        print("\n===== PnL REPORT =====", flush=True)
        print(f"Cash:         {portfolio.cash:.2f}", flush=True)
        print(f"BTC Price:    {current_price:.2f}", flush=True)
        print(f"BTC Position: {portfolio.asset:g}", flush=True)
        print(f"Trades:       {len(self.trades)}", flush=True)
        print(f"Total Value:  {total:.2f}", flush=True)
        print(f"PnL:          {self.pnl(portfolio, current_price):+.2f}", flush=True)
        print("======================\n", flush=True)

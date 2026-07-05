"""In-memory portfolio state."""

from core.event_bus import Event


class Portfolio:
    def __init__(self, cash: float = 10_000.0, asset: float = 0.0) -> None:
        self.cash = cash
        self.asset = asset
        self.last_price: float | None = None

    def total_value(self, price: float) -> float:
        return self.cash + self.asset * price

    def on_market_price(self, event: Event) -> None:
        symbol = str(event["symbol"])
        price = float(event["price"])
        self.last_price = price
        print(
            f"[PORTFOLIO] {symbol} price={price:.2f} | "
            f"Position={self.asset:g} | Cash={self.cash:.2f} | "
            f"Total={self.total_value(price):.2f}",
            flush=True,
        )

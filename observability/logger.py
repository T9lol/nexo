"""Console logger used by the simulator."""


class Logger:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}", flush=True)

    def trade(
        self,
        action: str,
        symbol: str,
        price: float,
        amount: float,
        strategy: str = "unknown",
    ) -> None:
        print(
            f"[TRADE][{strategy}] {action} {amount:g} {symbol} @ {price:.2f}",
            flush=True,
        )

    def risk(self, message: str) -> None:
        print(f"[RISK ALERT] {message}", flush=True)

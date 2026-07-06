"""Console logger used by the simulator."""


class Logger:
    def __init__(self, quiet: bool = False) -> None:
        # A quiet logger suppresses console output; used by the dashboard
        # runtime provider so live ticks don't spam the server console.
        self.quiet = quiet

    def log(self, message: str) -> None:
        if self.quiet:
            return
        print(f"[LOG] {message}", flush=True)

    def trade(
        self,
        action: str,
        symbol: str,
        price: float,
        amount: float,
        strategy: str = "unknown",
    ) -> None:
        if self.quiet:
            return
        print(
            f"[TRADE][{strategy}] {action} {amount:g} {symbol} @ {price:.2f}",
            flush=True,
        )

    def risk(self, message: str) -> None:
        if self.quiet:
            return
        print(f"[RISK ALERT] {message}", flush=True)

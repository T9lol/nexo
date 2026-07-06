"""Alert delivery boundary."""


class AlertSystem:
    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def send(self, message: str) -> None:
        if self.quiet:
            return
        print(f"[ALERT] {message}", flush=True)

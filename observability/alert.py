"""Alert delivery boundary."""


class AlertSystem:
    def send(self, message: str) -> None:
        print(f"[ALERT] {message}", flush=True)

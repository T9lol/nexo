import unittest

from core import EventBus


class EventBusTests(unittest.TestCase):
    def test_publish_delivers_event_to_subscriber(self) -> None:
        bus = EventBus()
        received: list[dict[str, object]] = []
        bus.subscribe("TEST", received.append)

        bus.publish("TEST", {"value": 42})

        self.assertEqual(received, [{"value": 42}])

    def test_unknown_event_has_no_effect(self) -> None:
        EventBus().publish("UNKNOWN", {"value": 42})


if __name__ == "__main__":
    unittest.main()

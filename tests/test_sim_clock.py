import pytest

from microfactory.sim.clock import LogicalClock
from microfactory.sim.events import SimEvent, event_digest


def test_clock_is_monotonic():
    clock = LogicalClock()
    assert clock.now == 0
    assert clock.advance() == 1
    assert clock.advance(4) == 5
    assert clock.advance_to(8) == 8
    with pytest.raises(ValueError, match="backwards"):
        clock.advance_to(7)


def test_event_order_and_digest_are_stable():
    events = [
        SimEvent(1, 2, "B", "x", {"z": 1}),
        SimEvent(0, 1, "A", "x", {"a": [2, 1]}),
    ]
    first = event_digest(events)
    second = event_digest(list(reversed(events)))
    assert first == second
    assert len(first) == 64

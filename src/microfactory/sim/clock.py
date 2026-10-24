from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LogicalClock:
    _tick: int = 0

    def __post_init__(self) -> None:
        if self._tick < 0:
            raise ValueError("initial tick must be non-negative")

    @property
    def now(self) -> int:
        return self._tick

    def advance(self, steps: int = 1) -> int:
        if steps < 0:
            raise ValueError("steps must be non-negative")
        self._tick += steps
        return self._tick

    def advance_to(self, tick: int) -> int:
        if tick < self._tick:
            raise ValueError("logical time cannot move backwards")
        self._tick = tick
        return self._tick

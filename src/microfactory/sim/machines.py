from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import Random


class MachineState(str, Enum):
    READY = "READY"
    BUSY = "BUSY"
    FAULTED = "FAULTED"


@dataclass(frozen=True, slots=True)
class MachineCompletion:
    machine_id: str
    task_id: str
    tick: int
    succeeded: bool


class SimulatedMachine:
    def __init__(
        self,
        machine_id: str,
        *,
        min_duration_ticks: int,
        max_duration_ticks: int,
        failure_probability: float = 0.0,
        seed: int = 0,
    ) -> None:
        if min_duration_ticks <= 0 or max_duration_ticks < min_duration_ticks:
            raise ValueError("invalid duration range")
        if not 0.0 <= failure_probability <= 1.0:
            raise ValueError("failure_probability must be between 0 and 1")
        self.machine_id = machine_id
        self.min_duration_ticks = min_duration_ticks
        self.max_duration_ticks = max_duration_ticks
        self.failure_probability = failure_probability
        self.state = MachineState.READY
        self._rng = Random(seed)
        self._task_id: str | None = None
        self._complete_at: int | None = None
        self._will_fail = False

    @property
    def task_id(self) -> str | None:
        return self._task_id

    @property
    def complete_at(self) -> int | None:
        return self._complete_at

    def start(self, task_id: str, tick: int) -> int:
        if tick < 0:
            raise ValueError("tick must be non-negative")
        if self.state is not MachineState.READY:
            raise ValueError(f"machine {self.machine_id!r} is not ready")
        duration = self._rng.randint(self.min_duration_ticks, self.max_duration_ticks)
        self._will_fail = self._rng.random() < self.failure_probability
        self._task_id = task_id
        self._complete_at = tick + duration
        self.state = MachineState.BUSY
        return self._complete_at

    def poll(self, tick: int) -> MachineCompletion | None:
        if self.state is not MachineState.BUSY:
            return None
        assert self._complete_at is not None
        assert self._task_id is not None
        if tick < self._complete_at:
            return None
        completion = MachineCompletion(
            machine_id=self.machine_id,
            task_id=self._task_id,
            tick=self._complete_at,
            succeeded=not self._will_fail,
        )
        self.state = MachineState.READY if completion.succeeded else MachineState.FAULTED
        self._task_id = None
        self._complete_at = None
        self._will_fail = False
        return completion

    def reset_fault(self) -> None:
        if self.state is not MachineState.FAULTED:
            raise ValueError("machine is not faulted")
        self.state = MachineState.READY

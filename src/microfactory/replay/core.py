from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from microfactory.sim.events import SimEvent, event_digest


@dataclass(frozen=True, slots=True)
class MachineReplayState:
    state: str
    task_id: str | None = None


@dataclass(frozen=True, slots=True)
class ReplayReport:
    digest: str
    event_count: int
    final_tick: int
    complete: bool
    machines: dict[str, MachineReplayState]


def _validate_event_order(events: list[SimEvent]) -> None:
    if not events:
        raise ValueError("event stream is empty")
    ordered = sorted(events)
    if events != ordered:
        raise ValueError("event stream must be ordered by tick/sequence")
    sequences = [event.sequence for event in events]
    if len(sequences) != len(set(sequences)):
        raise ValueError("event sequence numbers must be unique")
    if sequences != sorted(sequences):
        raise ValueError("event sequence numbers must be monotonic")


def replay_simulation_events(
    events: Iterable[SimEvent],
    *,
    expected_digest: str | None = None,
) -> ReplayReport:
    stream = list(events)
    _validate_event_order(stream)
    if stream[0].kind != "WORLD_INITIALIZED":
        raise ValueError("event stream must start with WORLD_INITIALIZED")

    machines: dict[str, MachineReplayState] = {}
    complete = False
    final_tick = stream[-1].tick

    for event in stream:
        if event.kind == "MACHINE_STARTED":
            task_id = str(event.payload["task_id"])
            current = machines.get(event.aggregate_id)
            if current is not None and current.state == "BUSY":
                raise ValueError(f"machine {event.aggregate_id!r} started while busy")
            machines[event.aggregate_id] = MachineReplayState("BUSY", task_id)
        elif event.kind == "MACHINE_SUCCEEDED":
            current = machines.get(event.aggregate_id)
            if current is None or current.state != "BUSY":
                raise ValueError(f"machine {event.aggregate_id!r} succeeded without BUSY state")
            if current.task_id != str(event.payload["task_id"]):
                raise ValueError("machine completion task_id does not match active task")
            machines[event.aggregate_id] = MachineReplayState("READY", None)
        elif event.kind == "MACHINE_FAILED":
            current = machines.get(event.aggregate_id)
            if current is None or current.state != "BUSY":
                raise ValueError(f"machine {event.aggregate_id!r} failed without BUSY state")
            if current.task_id != str(event.payload["task_id"]):
                raise ValueError("machine failure task_id does not match active task")
            machines[event.aggregate_id] = MachineReplayState("FAULTED", None)
        elif event.kind == "SCENARIO_COMPLETE":
            if event is not stream[-1]:
                raise ValueError("SCENARIO_COMPLETE must be the final event")
            complete = True

    digest = event_digest(stream)
    if expected_digest is not None and digest != expected_digest:
        raise ValueError(f"event digest mismatch: expected {expected_digest}, got {digest}")
    return ReplayReport(digest, len(stream), final_tick, complete, dict(sorted(machines.items())))


def canonical_replay_json(report: ReplayReport) -> str:
    payload = {
        "digest": report.digest,
        "event_count": report.event_count,
        "final_tick": report.final_tick,
        "complete": report.complete,
        "machines": {
            machine_id: {"state": state.state, "task_id": state.task_id}
            for machine_id, state in sorted(report.machines.items())
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def replay_report_digest(report: ReplayReport) -> str:
    return sha256(canonical_replay_json(report).encode("utf-8")).hexdigest()

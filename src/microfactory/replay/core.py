from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Protocol

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


class PersistedRecord(Protocol):
    timestamp_ns: int
    event_type: str
    aggregate_id: str
    correlation_id: str
    trace_id: str | None
    span_id: str | None
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PersistedReplayReport:
    digest: str
    record_count: int
    final_timestamp_ns: int
    correlation_id: str
    aggregate_states: dict[str, str]
    event_types: tuple[str, ...]


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


def persisted_record_digest(records: Iterable[PersistedRecord]) -> str:
    canonical = [
        {
            "timestamp_ns": record.timestamp_ns,
            "event_type": record.event_type,
            "aggregate_id": record.aggregate_id,
            "correlation_id": record.correlation_id,
            "trace_id": record.trace_id,
            "span_id": record.span_id,
            "payload": record.payload,
        }
        for record in records
    ]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def replay_persisted_records(
    records: Iterable[PersistedRecord],
    *,
    expected_digest: str | None = None,
) -> PersistedReplayReport:
    """Replay one persisted correlation stream across service boundaries."""
    stream = list(records)
    if not stream:
        raise ValueError("persisted record stream is empty")
    timestamps = [record.timestamp_ns for record in stream]
    if timestamps != sorted(timestamps):
        raise ValueError("persisted record stream must be ordered by timestamp")
    correlations = {record.correlation_id for record in stream}
    if len(correlations) != 1:
        raise ValueError("persisted record stream must contain one correlation_id")

    states: dict[str, str] = {}
    for record in stream:
        key = record.aggregate_id
        if record.event_type == "JOB_SUBMITTED":
            states[key] = str(record.payload.get("state", "SUBMITTED"))
        elif record.event_type == "TASK_STATE_CHANGED":
            task_id = str(record.payload["task_id"])
            states[f"{key}:{task_id}"] = str(record.payload["to"])
        elif record.event_type.startswith("RUNTIME_"):
            states[key] = str(record.payload.get("state", record.event_type.removeprefix("RUNTIME_")))
        elif record.event_type == "VISION_VERIFICATION":
            states[key] = str(record.payload["decision"])

    digest = persisted_record_digest(stream)
    if expected_digest is not None and digest != expected_digest:
        raise ValueError(f"persisted record digest mismatch: expected {expected_digest}, got {digest}")
    return PersistedReplayReport(
        digest=digest,
        record_count=len(stream),
        final_timestamp_ns=stream[-1].timestamp_ns,
        correlation_id=next(iter(correlations)),
        aggregate_states=dict(sorted(states.items())),
        event_types=tuple(record.event_type for record in stream),
    )


@dataclass(frozen=True, slots=True)
class ReplayDivergence:
    index: int
    reason: str
    left: SimEvent | None
    right: SimEvent | None


def first_replay_divergence(
    left_events: Iterable[SimEvent],
    right_events: Iterable[SimEvent],
) -> ReplayDivergence | None:
    """Return the first structural difference between two event streams.

    This is a debugging helper for deterministic replay: it intentionally
    reports the earliest causal divergence rather than only a final digest
    mismatch.
    """
    left = list(left_events)
    right = list(right_events)
    limit = max(len(left), len(right))
    for index in range(limit):
        a = left[index] if index < len(left) else None
        b = right[index] if index < len(right) else None
        if a is None or b is None:
            return ReplayDivergence(index, "stream_length", a, b)
        if a.tick != b.tick:
            return ReplayDivergence(index, "tick", a, b)
        if a.sequence != b.sequence:
            return ReplayDivergence(index, "sequence", a, b)
        if a.kind != b.kind:
            return ReplayDivergence(index, "kind", a, b)
        if a.aggregate_id != b.aggregate_id:
            return ReplayDivergence(index, "aggregate_id", a, b)
        if a.payload != b.payload:
            return ReplayDivergence(index, "payload", a, b)
    return None

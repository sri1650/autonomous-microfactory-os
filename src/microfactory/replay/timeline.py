from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from microfactory.sim.events import SimEvent


@dataclass(frozen=True, slots=True)
class TimelineFrame:
    index: int
    tick: int
    event_kind: str
    aggregate_id: str
    summary: str
    machine_states: dict[str,str]


def build_timeline(events: Iterable[SimEvent]) -> list[TimelineFrame]:
    states={}
    frames=[]
    for idx,event in enumerate(events):
        if event.kind=="MACHINE_STARTED":
            states[event.aggregate_id]="BUSY"
        elif event.kind=="MACHINE_SUCCEEDED":
            states[event.aggregate_id]="READY"
        elif event.kind=="MACHINE_FAILED":
            states[event.aggregate_id]="FAULTED"
        summary=f"{event.kind} · {event.aggregate_id}"
        if "task_id" in event.payload:
            summary += f" · {event.payload['task_id']}"
        frames.append(TimelineFrame(idx,event.tick,event.kind,event.aggregate_id,summary,dict(sorted(states.items()))))
    return frames

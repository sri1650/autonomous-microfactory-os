from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True, order=True, slots=True)
class SimEvent:
    tick: int
    sequence: int
    kind: str
    aggregate_id: str
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def canonical(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "sequence": self.sequence,
            "kind": self.kind,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
        }


def event_digest(events: list[SimEvent]) -> str:
    canonical = [event.canonical() for event in sorted(events)]
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from microfactory.domain.models import JobRecord, ResourceRecord, ResourceState


@dataclass(slots=True)
class InMemoryJobRepository:
    _jobs: dict[str, JobRecord] = field(default_factory=dict)

    def get(self, job_id: str) -> JobRecord | None:
        job = self._jobs.get(job_id)
        return deepcopy(job) if job is not None else None

    def save(self, job: JobRecord) -> None:
        job.validate_dag()
        self._jobs[job.job_id] = deepcopy(job)


@dataclass(slots=True)
class InMemoryResourceRepository:
    _resources: dict[str, ResourceRecord] = field(default_factory=dict)

    def get(self, resource_id: str) -> ResourceRecord | None:
        resource = self._resources.get(resource_id)
        return deepcopy(resource) if resource is not None else None

    def save(self, resource: ResourceRecord) -> None:
        self._resources[resource.resource_id] = deepcopy(resource)

    def list_available(self, resource_type: str) -> Sequence[ResourceRecord]:
        matches = [
            deepcopy(resource)
            for resource in self._resources.values()
            if resource.resource_type == resource_type
            and resource.state is ResourceState.AVAILABLE
        ]
        return tuple(sorted(matches, key=lambda item: item.resource_id))


@dataclass(frozen=True, slots=True)
class CapturedEvent:
    event_type: str
    aggregate_id: str
    payload: dict[str, Any]


@dataclass(slots=True)
class InMemoryEventSink:
    events: list[CapturedEvent] = field(default_factory=list)

    def append(
        self,
        *,
        event_type: str,
        aggregate_id: str,
        payload: Mapping[str, Any],
    ) -> None:
        self.events.append(
            CapturedEvent(
                event_type=event_type,
                aggregate_id=aggregate_id,
                payload=deepcopy(dict(payload)),
            )
        )

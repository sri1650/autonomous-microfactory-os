from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from .models import JobRecord, ResourceRecord


@runtime_checkable
class JobRepository(Protocol):
    def get(self, job_id: str) -> JobRecord | None: ...

    def save(self, job: JobRecord) -> None: ...


@runtime_checkable
class ResourceRepository(Protocol):
    def get(self, resource_id: str) -> ResourceRecord | None: ...

    def save(self, resource: ResourceRecord) -> None: ...

    def list_available(self, resource_type: str) -> Sequence[ResourceRecord]: ...


@runtime_checkable
class EventSink(Protocol):
    def append(
        self,
        *,
        event_type: str,
        aggregate_id: str,
        payload: Mapping[str, Any],
    ) -> None: ...

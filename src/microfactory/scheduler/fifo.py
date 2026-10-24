from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from microfactory.domain.models import JobRecord, ResourceRecord, ResourceState, TaskState


@dataclass(frozen=True, slots=True)
class Assignment:
    job_id: str
    task_id: str
    resource_id: str


def schedule_fifo(jobs: Sequence[JobRecord], resources: Sequence[ResourceRecord]) -> list[Assignment]:
    """Priority-first, creation-order-stable baseline scheduler.

    Job sequence order is treated as creation order. This function is pure: it
    returns proposed assignments and does not mutate jobs/resources.
    """
    available = [resource for resource in resources if resource.state is ResourceState.AVAILABLE]
    available.sort(key=lambda resource: resource.resource_id)
    claimed: set[str] = set()
    assignments: list[Assignment] = []

    indexed_jobs = list(enumerate(jobs))
    indexed_jobs.sort(key=lambda pair: (-pair[1].priority, pair[0]))

    for _, job in indexed_jobs:
        for task_id, task in job.tasks.items():
            if task.state is not TaskState.READY:
                continue
            required_caps = frozenset(task.definition.payload.get("required_capabilities", ()))
            candidate = next(
                (
                    resource
                    for resource in available
                    if resource.resource_id not in claimed
                    and resource.resource_type == task.definition.required_resource_type
                    and required_caps.issubset(resource.capabilities)
                ),
                None,
            )
            if candidate is None:
                continue
            claimed.add(candidate.resource_id)
            assignments.append(Assignment(job.job_id, task_id, candidate.resource_id))

    return assignments

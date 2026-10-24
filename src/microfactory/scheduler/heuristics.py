from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from microfactory.domain.models import JobRecord, ResourceRecord, ResourceState, TaskRecord, TaskState
from .fifo import Assignment


class Heuristic(str, Enum):
    PRIORITY = "priority"
    SHORTEST_PROCESSING_TIME = "spt"
    EARLIEST_DUE_DATE = "edd"
    WEIGHTED = "weighted"


@dataclass(frozen=True, slots=True)
class RankedTask:
    job: JobRecord
    task_id: str
    task: TaskRecord
    rank_key: tuple[float, ...]


def _duration(task: TaskRecord) -> float:
    value = float(task.definition.payload.get("duration", 1.0))
    if value < 0:
        raise ValueError("task duration cannot be negative")
    return value


def _due_tick(task: TaskRecord) -> float:
    return float(task.definition.payload.get("due_tick", float("inf")))


def _travel_cost(task: TaskRecord) -> float:
    value = float(task.definition.payload.get("travel_cost", 0.0))
    if value < 0:
        raise ValueError("travel_cost cannot be negative")
    return value


def _rank(job_index: int, job: JobRecord, task_index: int, task: TaskRecord, strategy: Heuristic):
    duration = _duration(task)
    due = _due_tick(task)
    travel = _travel_cost(task)
    if strategy is Heuristic.PRIORITY:
        return (-float(job.priority), float(job_index), float(task_index))
    if strategy is Heuristic.SHORTEST_PROCESSING_TIME:
        return (duration, -float(job.priority), float(job_index), float(task_index))
    if strategy is Heuristic.EARLIEST_DUE_DATE:
        return (due, -float(job.priority), duration, float(job_index), float(task_index))
    if strategy is Heuristic.WEIGHTED:
        score = duration + 0.5 * travel - 2.0 * float(job.priority)
        return (score, due, float(job_index), float(task_index))
    raise ValueError(f"unsupported heuristic {strategy!r}")


def rank_ready_tasks(jobs: Sequence[JobRecord], strategy: Heuristic) -> list[RankedTask]:
    ranked: list[RankedTask] = []
    for job_index, job in enumerate(jobs):
        for task_index, (task_id, task) in enumerate(job.tasks.items()):
            if task.state is not TaskState.READY:
                continue
            ranked.append(
                RankedTask(job, task_id, task, _rank(job_index, job, task_index, task, strategy))
            )
    ranked.sort(key=lambda item: item.rank_key)
    return ranked


def schedule_heuristic(
    jobs: Sequence[JobRecord],
    resources: Sequence[ResourceRecord],
    *,
    strategy: Heuristic,
) -> list[Assignment]:
    available = sorted(
        (r for r in resources if r.state is ResourceState.AVAILABLE),
        key=lambda r: r.resource_id,
    )
    claimed: set[str] = set()
    out: list[Assignment] = []

    for item in rank_ready_tasks(jobs, strategy):
        required_caps = frozenset(item.task.definition.payload.get("required_capabilities", ()))
        resource = next(
            (
                r for r in available
                if r.resource_id not in claimed
                and r.resource_type == item.task.definition.required_resource_type
                and required_caps.issubset(r.capabilities)
            ),
            None,
        )
        if resource is None:
            continue
        claimed.add(resource.resource_id)
        out.append(Assignment(item.job.job_id, item.task_id, resource.resource_id))
    return out

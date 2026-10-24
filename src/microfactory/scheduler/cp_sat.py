from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from microfactory.domain.models import JobRecord, ResourceRecord, ResourceState, TaskState


@dataclass(frozen=True, slots=True)
class SchedTask:
    job_id: str
    task_id: str
    duration: int
    resource_type: str
    dependencies: tuple[tuple[str,str], ...]
    priority: int
    due_tick: int | None


@dataclass(frozen=True, slots=True)
class SchedulingProblem:
    tasks: tuple[SchedTask, ...]
    capacities: dict[str,int]


def build_problem(jobs: Sequence[JobRecord], resources: Sequence[ResourceRecord]) -> SchedulingProblem:
    capacities: dict[str,int]={}
    for r in resources:
        if r.state is ResourceState.OFFLINE or r.state is ResourceState.FAULTED:
            continue
        capacities[r.resource_type]=capacities.get(r.resource_type,0)+1

    tasks=[]
    for job in jobs:
        for task_id, task in job.tasks.items():
            if task.state in {TaskState.SUCCEEDED,TaskState.CANCELLED}:
                continue
            duration=int(task.definition.payload.get("duration",1))
            if duration <= 0:
                raise ValueError("CP-SAT duration must be a positive integer")
            due=task.definition.payload.get("due_tick")
            due_tick=int(due) if due is not None else None
            deps=tuple((job.job_id,dep) for dep in task.definition.dependencies)
            tasks.append(SchedTask(
                job.job_id,task_id,duration,task.definition.required_resource_type,
                deps,job.priority,due_tick
            ))
    tasks.sort(key=lambda t:(t.job_id,t.task_id))
    return SchedulingProblem(tuple(tasks),dict(sorted(capacities.items())))


def solve_cp_sat(problem: SchedulingProblem):
    """Solve via OR-Tools when the optional dependency is installed.

    The model/extraction boundary is fully tested without OR-Tools. Work/Codex
    should implement and integration-test this function in the environment that
    provides `ortools`.
    """
    try:
        from ortools.sat.python import cp_model  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OR-Tools is not installed; CP-SAT solving is reserved for the Work/Codex integration environment"
        ) from exc

    # Intentionally fail loudly rather than pretending an unverified optimiser
    # exists. The task graph requires Codex to finish the real model.
    raise NotImplementedError("CP-SAT solve model is intentionally reserved for M5-T02")

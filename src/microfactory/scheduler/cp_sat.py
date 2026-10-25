from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
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


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    job_id: str
    task_id: str
    resource_type: str
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class ScheduleSolution:
    tasks: tuple[ScheduledTask, ...]
    makespan: int
    total_tardiness: int
    weighted_tardiness: int
    solver_ms: float
    optimal: bool


class SchedulingInfeasibleError(RuntimeError):
    pass


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


def solve_cp_sat(problem: SchedulingProblem) -> ScheduleSolution:
    """Solve dependency and resource-capacity scheduling deterministically."""
    try:
        from ortools.sat.python import cp_model  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OR-Tools is not installed; CP-SAT solving is reserved for the Work/Codex integration environment"
        ) from exc

    if not problem.tasks:
        return ScheduleSolution((), 0, 0, 0, 0.0, True)

    model = cp_model.CpModel()
    horizon = sum(task.duration for task in problem.tasks)
    keys = {(task.job_id, task.task_id): task for task in problem.tasks}
    starts = {}
    ends = {}
    intervals_by_resource: dict[str, list] = {}

    for task in problem.tasks:
        key = (task.job_id, task.task_id)
        name = f"{task.job_id}:{task.task_id}"
        starts[key] = model.new_int_var(0, horizon, f"start:{name}")
        ends[key] = model.new_int_var(0, horizon, f"end:{name}")
        interval = model.new_interval_var(
            starts[key], task.duration, ends[key], f"interval:{name}"
        )
        intervals_by_resource.setdefault(task.resource_type, []).append(interval)

    for task in problem.tasks:
        key = (task.job_id, task.task_id)
        for dependency in task.dependencies:
            if dependency not in keys:
                raise ValueError(
                    f"unknown dependency {dependency!r} for task {key!r}"
                )
            model.add(starts[key] >= ends[dependency])

    for resource_type, intervals in intervals_by_resource.items():
        capacity = problem.capacities.get(resource_type, 0)
        if capacity <= 0:
            raise SchedulingInfeasibleError(
                f"no online capacity for resource type {resource_type!r}"
            )
        model.add_cumulative(intervals, [1] * len(intervals), capacity)

    makespan = model.new_int_var(0, horizon, "makespan")
    model.add_max_equality(makespan, list(ends.values()))
    tardiness_vars = []
    weighted_terms = []
    for task in problem.tasks:
        if task.due_tick is None:
            continue
        key = (task.job_id, task.task_id)
        tardiness = model.new_int_var(0, horizon, f"tardiness:{task.job_id}:{task.task_id}")
        model.add_max_equality(tardiness, [ends[key] - task.due_tick, 0])
        tardiness_vars.append(tardiness)
        weighted_terms.append(tardiness * max(1, task.priority))

    makespan_weight = horizon * sum(max(1, task.priority) for task in problem.tasks) + 1
    model.minimize(makespan * makespan_weight + sum(weighted_terms))

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    started = perf_counter()
    status = solver.solve(model)
    elapsed_ms = (perf_counter() - started) * 1_000
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise SchedulingInfeasibleError(f"CP-SAT status {solver.status_name(status)}")

    scheduled = tuple(
        ScheduledTask(
            task.job_id,
            task.task_id,
            task.resource_type,
            solver.value(starts[(task.job_id, task.task_id)]),
            solver.value(ends[(task.job_id, task.task_id)]),
        )
        for task in problem.tasks
    )
    tardiness_values = [solver.value(value) for value in tardiness_vars]
    weighted_tardiness = sum(
        max(0, item.end - task.due_tick) * max(1, task.priority)
        for task, item in zip(problem.tasks, scheduled, strict=True)
        if task.due_tick is not None
    )
    return ScheduleSolution(
        scheduled,
        solver.value(makespan),
        sum(tardiness_values),
        weighted_tardiness,
        round(elapsed_ms, 3),
        status == cp_model.OPTIMAL,
    )

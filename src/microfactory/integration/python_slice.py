from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.domain.models import (
    JobRecord,
    JobState,
    ResourceRecord,
    TaskDefinition,
    TaskRecord,
    TaskState,
)
from microfactory.fleet.cbs import first_conflict
from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively
from microfactory.fleet.grid import Grid
from microfactory.orchestrator import Orchestrator
from microfactory.scheduler.fifo import schedule_fifo
from microfactory.vision.contracts import AlignmentResult, VerificationDecision
from microfactory.vision.verification import VerificationThresholds, decide_verification


@dataclass(frozen=True, slots=True)
class PythonSliceResult:
    jobs: dict[str, JobRecord]
    routes: dict[str, list[tuple[int, int]]]
    events: int
    scheduler_rounds: int


def _job(job_id: str, priority: int, goal: tuple[int, int]) -> JobRecord:
    move_id = f"{job_id}-move"
    inspect_id = f"{job_id}-inspect"
    return JobRecord(
        job_id=job_id,
        priority=priority,
        tasks={
            move_id: TaskRecord(
                TaskDefinition(
                    move_id,
                    "MOVE",
                    "mover",
                    payload={"goal": list(goal)},
                )
            ),
            inspect_id: TaskRecord(
                TaskDefinition(
                    inspect_id,
                    "INSPECT",
                    "vision",
                    dependencies=(move_id,),
                )
            ),
        },
    )


def run_python_vertical_slice(path: str | Path) -> PythonSliceResult:
    """Exercise the current Python layers before Rust/DB/CP-SAT integration.

    This is deliberately a pre-integration vertical slice. It proves domain,
    FIFO scheduling, conflict-free mover routing, vision policy and job
    lifecycle compose correctly. It is not the final M9 E2E milestone because
    it does not yet include Rust runtime, CP-SAT, PostgreSQL or ClickHouse.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    grid = Grid(
        int(raw["grid"]["width"]),
        int(raw["grid"]["height"]),
        frozenset(tuple(cell) for cell in raw["grid"].get("blocked", [])),
    )
    robot_positions = {rid: tuple(cell) for rid, cell in raw["robots"].items()}

    jobs_repo = InMemoryJobRepository()
    event_sink = InMemoryEventSink()
    service = Orchestrator(jobs_repo, event_sink)

    job_ids = []
    for spec in raw["jobs"]:
        job = _job(str(spec["id"]), int(spec["priority"]), tuple(spec["goal"]))
        job_ids.append(job.job_id)
        service.submit_job(job, command_id=f"submit:{job.job_id}")

    mover_resources = [
        ResourceRecord(resource_id, "mover") for resource_id in sorted(robot_positions)
    ]
    vision_resources = [ResourceRecord("vision-1", "vision")]

    # Round 1: all mover tasks are ready and there are three mover resources.
    current_jobs = [service.get_job(job_id) for job_id in job_ids]
    mover_assignments = schedule_fifo(current_jobs, mover_resources)
    if len(mover_assignments) != len(job_ids):
        raise RuntimeError("expected one mover assignment per job")

    requests = []
    by_robot_assignment = {}
    for assignment in mover_assignments:
        job = service.get_job(assignment.job_id)
        task = job.tasks[assignment.task_id]
        goal = tuple(task.definition.payload["goal"])
        requests.append(
            RobotPlanRequest(
                assignment.resource_id,
                robot_positions[assignment.resource_id],
                goal,
                priority=job.priority,
            )
        )
        by_robot_assignment[assignment.resource_id] = assignment

    routes, _ = plan_cooperatively(grid, requests, max_time=60)
    if first_conflict(routes) is not None:
        raise RuntimeError("fleet plan contains a conflict")

    for robot_id in sorted(routes):
        assignment = by_robot_assignment[robot_id]
        service.transition_task(
            assignment.job_id,
            assignment.task_id,
            TaskState.ASSIGNED,
            command_id=f"assign:{assignment.task_id}",
            resource_id=robot_id,
        )
        service.transition_task(
            assignment.job_id,
            assignment.task_id,
            TaskState.EXECUTING,
            command_id=f"execute:{assignment.task_id}",
        )
        service.transition_task(
            assignment.job_id,
            assignment.task_id,
            TaskState.SUCCEEDED,
            command_id=f"succeed:{assignment.task_id}",
        )
        robot_positions[robot_id] = routes[robot_id][-1]

    thresholds = VerificationThresholds(**raw["vision"])
    nominal_alignment = AlignmentResult(
        expected_center_px=(100.0, 100.0),
        measured_center_px=(100.5, 99.5),
        expected_angle_deg=0.0,
        measured_angle_deg=0.5,
        dx_px=0.5,
        dy_px=-0.5,
        position_error_px=0.707,
        angle_error_deg=0.5,
        confidence=0.95,
        foreground_pixels=100,
    )
    decision = decide_verification(nominal_alignment, thresholds)
    if decision.decision is not VerificationDecision.PASS:
        raise RuntimeError("nominal vision fixture must pass")

    scheduler_rounds = 1
    remaining = set(job_ids)
    while remaining:
        scheduler_rounds += 1
        current_jobs = [service.get_job(job_id) for job_id in sorted(remaining)]
        assignments = schedule_fifo(current_jobs, vision_resources)
        if not assignments:
            raise RuntimeError("vision scheduling made no progress")
        assignment = assignments[0]
        service.transition_task(
            assignment.job_id,
            assignment.task_id,
            TaskState.ASSIGNED,
            command_id=f"assign:{assignment.task_id}",
            resource_id=assignment.resource_id,
        )
        service.transition_task(
            assignment.job_id,
            assignment.task_id,
            TaskState.EXECUTING,
            command_id=f"execute:{assignment.task_id}",
        )
        service.transition_task(
            assignment.job_id,
            assignment.task_id,
            TaskState.SUCCEEDED,
            command_id=f"succeed:{assignment.task_id}",
        )
        if service.get_job(assignment.job_id).state is JobState.SUCCEEDED:
            remaining.remove(assignment.job_id)

    final_jobs = {job_id: service.get_job(job_id) for job_id in job_ids}
    return PythonSliceResult(final_jobs, routes, len(event_sink.events), scheduler_rounds)

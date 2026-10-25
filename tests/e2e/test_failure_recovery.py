import json
from pathlib import Path

import pytest

from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.chaos.faults import Fault, FaultType, apply_fault_to_telemetry
from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord, TaskState
from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively
from microfactory.fleet.grid import Grid
from microfactory.fleet.health import HealthState, RobotTelemetry, assess_health, can_accept_mission
from microfactory.orchestrator import Orchestrator
from microfactory.vision.contracts import AlignmentResult, VerificationDecision
from microfactory.vision.verification import VerificationThresholds, decide_verification


ROOT = Path(__file__).parents[2]


def test_blocked_aisle_heartbeat_loss_and_failed_pick_recover_within_bounds():
    scenario = json.loads((ROOT / "scenarios/e2e/failure_recovery.json").read_text())
    request = RobotPlanRequest(
        scenario["robot"]["id"],
        tuple(scenario["robot"]["start"]),
        tuple(scenario["robot"]["goal"]),
    )
    blocked = Grid(
        scenario["grid"]["width"],
        scenario["grid"]["height"],
        frozenset(tuple(cell) for cell in scenario["grid"]["blocked"]),
    )
    with pytest.raises(ValueError, match="no time-feasible route"):
        plan_cooperatively(blocked, [request], max_time=20)

    recovered = Grid(
        scenario["grid"]["width"],
        scenario["grid"]["height"],
        frozenset(tuple(cell) for cell in scenario["recovery_blocked"]),
    )
    routes, _ = plan_cooperatively(recovered, [request], max_time=20)
    assert routes[request.robot_id][-1] == request.goal

    healthy = RobotTelemetry(request.robot_id, 90, 40, 10)
    lost = apply_fault_to_telemetry(
        healthy,
        Fault(
            scenario["heartbeat_fault"]["tick"],
            request.robot_id,
            FaultType.HEARTBEAT_LOSS,
            scenario["heartbeat_fault"]["magnitude"],
        ),
    )
    assert assess_health(lost).state is HealthState.OFFLINE
    assert not can_accept_mission(lost, distance_cells=len(routes[request.robot_id]) - 1)
    assert assess_health(healthy).state is HealthState.HEALTHY

    service = Orchestrator(InMemoryJobRepository(), InMemoryEventSink())
    job = JobRecord(
        "job-recovery",
        1,
        {"inspect": TaskRecord(TaskDefinition("inspect", "INSPECT", "vision"))},
    )
    service.submit_job(job, command_id="submit")
    service.transition_task("job-recovery", "inspect", TaskState.ASSIGNED, command_id="assign-1", resource_id="vision-1")
    service.transition_task("job-recovery", "inspect", TaskState.EXECUTING, command_id="execute-1")

    thresholds = VerificationThresholds(2, 5, 2, 5, 0.8, 0.4)
    failed_pick = AlignmentResult((0, 0), (3, 0), 0, 0, 3, 0, 3, 0, 0.9, 100)
    assert decide_verification(failed_pick, thresholds).decision is VerificationDecision.RETRY
    failed = service.transition_task("job-recovery", "inspect", TaskState.FAILED, command_id="fail-1")
    assert failed.job.state is JobState.FAILED

    for attempt in range(scenario["max_vision_retries"]):
        service.retry_task("job-recovery", "inspect", command_id=f"retry-{attempt + 1}")
        service.transition_task("job-recovery", "inspect", TaskState.ASSIGNED, command_id="assign-2", resource_id="vision-1")
        service.transition_task("job-recovery", "inspect", TaskState.EXECUTING, command_id="execute-2")
        result = service.transition_task("job-recovery", "inspect", TaskState.SUCCEEDED, command_id="succeed-2")
    assert result.job.state is JobState.SUCCEEDED
    assert result.job.tasks["inspect"].attempt == scenario["max_vision_retries"]

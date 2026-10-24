import pytest

from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord, TaskState
from microfactory.orchestrator import Orchestrator


def build_job(job_id: str = "job-1") -> JobRecord:
    return JobRecord(
        job_id=job_id,
        priority=10,
        tasks={
            "load": TaskRecord(TaskDefinition("load", "LOAD", "gantry")),
            "move": TaskRecord(TaskDefinition("move", "MOVE", "mover", ("load",))),
        },
    )


def make_service():
    jobs = InMemoryJobRepository()
    events = InMemoryEventSink()
    return Orchestrator(jobs, events), jobs, events


def test_submit_starts_job_and_initial_ready_task():
    svc, _, events = make_service()
    result = svc.submit_job(build_job(), command_id="cmd-submit")
    assert result.job.state is JobState.RUNNING
    assert result.job.tasks["load"].state is TaskState.READY
    assert result.job.tasks["move"].state is TaskState.PENDING
    assert events.events[-1].event_type == "JOB_SUBMITTED"


def test_submit_command_is_idempotent():
    svc, _, events = make_service()
    first = svc.submit_job(build_job(), command_id="same")
    second = svc.submit_job(build_job(), command_id="same")
    assert first.job == second.job
    assert second.replayed
    assert len(events.events) == 1


def test_reusing_command_id_for_different_operation_is_rejected():
    svc, _, _ = make_service()
    svc.submit_job(build_job(), command_id="same")
    with pytest.raises(ValueError, match="different operation"):
        svc.cancel_job("job-1", command_id="same")


def test_task_progression_unlocks_dependency_and_finishes_job():
    svc, _, _ = make_service()
    svc.submit_job(build_job(), command_id="submit")
    svc.transition_task("job-1", "load", TaskState.ASSIGNED, command_id="a1", resource_id="g1")
    svc.transition_task("job-1", "load", TaskState.EXECUTING, command_id="a2")
    after_load = svc.transition_task("job-1", "load", TaskState.SUCCEEDED, command_id="a3")
    assert after_load.job.tasks["move"].state is TaskState.READY
    svc.transition_task("job-1", "move", TaskState.ASSIGNED, command_id="m1", resource_id="r1")
    svc.transition_task("job-1", "move", TaskState.EXECUTING, command_id="m2")
    done = svc.transition_task("job-1", "move", TaskState.SUCCEEDED, command_id="m3")
    assert done.job.state is JobState.SUCCEEDED


def test_failed_task_can_retry_and_increments_attempt():
    svc, _, _ = make_service()
    svc.submit_job(build_job(), command_id="submit")
    svc.transition_task("job-1", "load", TaskState.ASSIGNED, command_id="a1", resource_id="g1")
    svc.transition_task("job-1", "load", TaskState.EXECUTING, command_id="a2")
    svc.transition_task("job-1", "load", TaskState.FAILED, command_id="a3")
    retried = svc.retry_task("job-1", "load", command_id="a4")
    assert retried.job.tasks["load"].state is TaskState.READY
    assert retried.job.tasks["load"].attempt == 1
    assert retried.job.tasks["load"].assigned_resource_id is None


def test_cancel_job_cancels_nonterminal_tasks():
    svc, _, events = make_service()
    svc.submit_job(build_job(), command_id="submit")
    result = svc.cancel_job("job-1", command_id="cancel")
    assert result.job.state is JobState.CANCELLED
    assert all(task.state is TaskState.CANCELLED for task in result.job.tasks.values())
    assert events.events[-1].event_type == "JOB_CANCELLED"


def test_terminal_failed_task_can_be_retried_and_reopens_job():
    svc, _, _ = make_service()
    svc.submit_job(build_job(), command_id="submit-terminal-retry")

    svc.transition_task("job-1", "load", TaskState.ASSIGNED, command_id="l1", resource_id="g1")
    svc.transition_task("job-1", "load", TaskState.EXECUTING, command_id="l2")
    svc.transition_task("job-1", "load", TaskState.SUCCEEDED, command_id="l3")

    svc.transition_task("job-1", "move", TaskState.ASSIGNED, command_id="m1", resource_id="r1")
    svc.transition_task("job-1", "move", TaskState.EXECUTING, command_id="m2")
    failed = svc.transition_task("job-1", "move", TaskState.FAILED, command_id="m3")
    assert failed.job.state is JobState.FAILED

    retried = svc.retry_task("job-1", "move", command_id="m4")
    assert retried.job.state is JobState.RUNNING
    assert retried.job.tasks["move"].state is TaskState.READY
    assert retried.job.tasks["move"].attempt == 1

    svc.transition_task("job-1", "move", TaskState.ASSIGNED, command_id="m5", resource_id="r1")
    svc.transition_task("job-1", "move", TaskState.EXECUTING, command_id="m6")
    done = svc.transition_task("job-1", "move", TaskState.SUCCEEDED, command_id="m7")
    assert done.job.state is JobState.SUCCEEDED

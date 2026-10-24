import pytest

from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord, TaskState
from microfactory.domain.transitions import assert_job_transition, assert_task_transition


def build_job() -> JobRecord:
    return JobRecord(
        job_id="job-1",
        priority=10,
        tasks={
            "load": TaskRecord(TaskDefinition("load", "LOAD", "gantry")),
            "move": TaskRecord(TaskDefinition("move", "MOVE", "mover", ("load",))),
            "inspect": TaskRecord(TaskDefinition("inspect", "VISION", "camera", ("move",))),
        },
    )


def test_refresh_ready_tasks_respects_dependencies():
    job = build_job()
    assert job.refresh_ready_tasks() == ["load"]
    assert job.tasks["load"].state is TaskState.READY
    job.tasks["load"].transition_to(TaskState.ASSIGNED)
    job.tasks["load"].transition_to(TaskState.EXECUTING)
    job.tasks["load"].transition_to(TaskState.SUCCEEDED)
    assert job.refresh_ready_tasks() == ["move"]


def test_task_transition_helper_rejects_illegal_transition():
    task = TaskRecord(TaskDefinition("x", "X", "machine"))
    with pytest.raises(ValueError, match="Illegal transition"):
        task.transition_to(TaskState.SUCCEEDED)


def test_unknown_dependency_is_rejected():
    job = JobRecord(
        job_id="bad",
        priority=1,
        tasks={"x": TaskRecord(TaskDefinition("x", "X", "machine", ("missing",)))},
    )
    with pytest.raises(ValueError, match="unknown dependencies"):
        job.validate_dag()


def test_cycle_is_rejected():
    job = JobRecord(
        job_id="cycle",
        priority=1,
        tasks={
            "a": TaskRecord(TaskDefinition("a", "A", "machine", ("b",))),
            "b": TaskRecord(TaskDefinition("b", "B", "machine", ("a",))),
        },
    )
    with pytest.raises(ValueError, match="cycle"):
        job.validate_dag()


def test_duplicate_definition_task_ids_are_rejected():
    job = JobRecord(
        job_id="dup",
        priority=1,
        tasks={
            "a": TaskRecord(TaskDefinition("same", "A", "machine")),
            "b": TaskRecord(TaskDefinition("same", "B", "machine")),
        },
    )
    with pytest.raises(ValueError, match="duplicate task IDs"):
        job.validate_dag()


def test_task_map_key_must_match_definition_id():
    job = JobRecord(
        job_id="mismatch",
        priority=1,
        tasks={"map-key": TaskRecord(TaskDefinition("definition-id", "A", "machine"))},
    )
    with pytest.raises(ValueError, match="does not match"):
        job.validate_dag()


def test_terminal_job_state_is_derived_only_after_all_tasks_terminal():
    job = build_job()
    assert job.derived_terminal_state() is None
    for task in job.tasks.values():
        task.state = TaskState.SUCCEEDED
    assert job.derived_terminal_state() is JobState.SUCCEEDED
    job.tasks["inspect"].state = TaskState.FAILED
    assert job.derived_terminal_state() is JobState.FAILED
    job.tasks["inspect"].state = TaskState.CANCELLED
    assert job.derived_terminal_state() is JobState.CANCELLED


def test_empty_job_is_terminal_success():
    job = JobRecord(job_id="empty", priority=1, tasks={})
    assert job.derived_terminal_state() is JobState.SUCCEEDED


def test_job_transition_rules():
    assert_job_transition(JobState.QUEUED, JobState.PLANNING)
    with pytest.raises(ValueError):
        assert_job_transition(JobState.QUEUED, JobState.SUCCEEDED)


def test_task_retry_transition_is_explicit():
    assert_task_transition(TaskState.FAILED, TaskState.READY)
    with pytest.raises(ValueError):
        assert_task_transition(TaskState.SUCCEEDED, TaskState.READY)

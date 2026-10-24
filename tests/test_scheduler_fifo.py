from microfactory.domain.models import (
    JobRecord,
    ResourceRecord,
    ResourceState,
    TaskDefinition,
    TaskRecord,
    TaskState,
)
from microfactory.scheduler import schedule_fifo


def ready_task(task_id: str, resource_type: str, *, capabilities=()):
    return TaskRecord(
        TaskDefinition(
            task_id,
            "WORK",
            resource_type,
            payload={"required_capabilities": list(capabilities)},
        ),
        state=TaskState.READY,
    )


def test_higher_priority_job_wins_single_resource():
    low = JobRecord("low", 1, {"a": ready_task("a", "mover")})
    high = JobRecord("high", 10, {"b": ready_task("b", "mover")})
    result = schedule_fifo([low, high], [ResourceRecord("r1", "mover")])
    assert [(x.job_id, x.task_id, x.resource_id) for x in result] == [("high", "b", "r1")]


def test_equal_priority_preserves_job_creation_order():
    first = JobRecord("first", 5, {"a": ready_task("a", "mover")})
    second = JobRecord("second", 5, {"b": ready_task("b", "mover")})
    result = schedule_fifo([first, second], [ResourceRecord("r1", "mover")])
    assert result[0].job_id == "first"


def test_resource_capabilities_are_respected():
    job = JobRecord(
        "j",
        1,
        {"camera-task": ready_task("camera-task", "camera", capabilities=("rgbd",))},
    )
    resources = [
        ResourceRecord("cam-1", "camera", capabilities=frozenset({"rgb"})),
        ResourceRecord("cam-2", "camera", capabilities=frozenset({"rgb", "rgbd"})),
    ]
    result = schedule_fifo([job], resources)
    assert result[0].resource_id == "cam-2"


def test_busy_resource_and_nonready_task_are_ignored():
    pending = TaskRecord(TaskDefinition("p", "WORK", "mover"), state=TaskState.PENDING)
    job = JobRecord("j", 1, {"p": pending})
    resources = [ResourceRecord("r1", "mover", state=ResourceState.BUSY)]
    assert schedule_fifo([job], resources) == []


def test_one_resource_is_not_double_booked_in_same_cycle():
    job = JobRecord(
        "j",
        1,
        {"a": ready_task("a", "mover"), "b": ready_task("b", "mover")},
    )
    result = schedule_fifo([job], [ResourceRecord("r1", "mover")])
    assert len(result) == 1

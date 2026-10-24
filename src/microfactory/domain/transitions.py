from __future__ import annotations

from .models import JobState, RobotMode, TaskState


_JOB_TRANSITIONS = {
    JobState.QUEUED: {JobState.PLANNING, JobState.CANCELLED},
    JobState.PLANNING: {JobState.RUNNING, JobState.FAILED, JobState.CANCELLED},
    JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: set(),
    JobState.CANCELLED: set(),
}

_TASK_TRANSITIONS = {
    TaskState.PENDING: {TaskState.READY, TaskState.CANCELLED},
    TaskState.READY: {TaskState.ASSIGNED, TaskState.CANCELLED},
    TaskState.ASSIGNED: {TaskState.EXECUTING, TaskState.READY, TaskState.CANCELLED},
    TaskState.EXECUTING: {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.SUCCEEDED: set(),
    TaskState.FAILED: {TaskState.READY},
    TaskState.CANCELLED: set(),
}

_ROBOT_TRANSITIONS = {
    RobotMode.OFFLINE: {RobotMode.IDLE},
    RobotMode.IDLE: {RobotMode.HOMING, RobotMode.READY, RobotMode.OFFLINE, RobotMode.ESTOP},
    RobotMode.HOMING: {RobotMode.READY, RobotMode.FAULTED, RobotMode.ESTOP},
    RobotMode.READY: {RobotMode.EXECUTING, RobotMode.PAUSED, RobotMode.FAULTED, RobotMode.ESTOP, RobotMode.OFFLINE},
    RobotMode.EXECUTING: {RobotMode.READY, RobotMode.PAUSED, RobotMode.FAULTED, RobotMode.ESTOP},
    RobotMode.PAUSED: {RobotMode.READY, RobotMode.EXECUTING, RobotMode.FAULTED, RobotMode.ESTOP},
    RobotMode.FAULTED: {RobotMode.IDLE, RobotMode.ESTOP, RobotMode.OFFLINE},
    RobotMode.ESTOP: {RobotMode.IDLE, RobotMode.OFFLINE},
}


def assert_transition(current, target, table) -> None:
    if target not in table[current]:
        raise ValueError(f"Illegal transition: {current.value} -> {target.value}")


def assert_job_transition(current: JobState, target: JobState) -> None:
    assert_transition(current, target, _JOB_TRANSITIONS)


def assert_task_transition(current: TaskState, target: TaskState) -> None:
    assert_transition(current, target, _TASK_TRANSITIONS)


def assert_robot_transition(current: RobotMode, target: RobotMode) -> None:
    assert_transition(current, target, _ROBOT_TRANSITIONS)

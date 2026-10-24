from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobState(str, Enum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskState(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RobotMode(str, Enum):
    OFFLINE = "OFFLINE"
    IDLE = "IDLE"
    HOMING = "HOMING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    PAUSED = "PAUSED"
    FAULTED = "FAULTED"
    ESTOP = "ESTOP"


class ResourceState(str, Enum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BUSY = "BUSY"
    FAULTED = "FAULTED"


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    task_id: str
    kind: str
    required_resource_type: str
    dependencies: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TaskRecord:
    definition: TaskDefinition
    state: TaskState = TaskState.PENDING
    attempt: int = 0
    assigned_resource_id: str | None = None

    def transition_to(self, target: TaskState) -> None:
        """Apply one validated state transition.

        The import is local so the transition table can remain isolated from
        the domain data definitions without introducing an import cycle.
        """
        from .transitions import assert_task_transition

        assert_task_transition(self.state, target)
        self.state = target


@dataclass(slots=True)
class ResourceRecord:
    resource_id: str
    resource_type: str
    state: ResourceState = ResourceState.AVAILABLE
    capabilities: frozenset[str] = frozenset()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobRecord:
    job_id: str
    priority: int
    tasks: dict[str, TaskRecord]
    state: JobState = JobState.QUEUED

    def validate_dag(self) -> None:
        task_ids = set(self.tasks)
        definition_ids = [record.definition.task_id for record in self.tasks.values()]

        if len(definition_ids) != len(set(definition_ids)):
            raise ValueError("Task graph contains duplicate task IDs")

        for key, record in self.tasks.items():
            if record.definition.task_id != key:
                raise ValueError(
                    f"Task map key {key!r} does not match definition ID "
                    f"{record.definition.task_id!r}"
                )
            unknown = set(record.definition.dependencies) - task_ids
            if unknown:
                raise ValueError(
                    f"Task {record.definition.task_id!r} has unknown dependencies: {sorted(unknown)}"
                )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("Task graph contains a cycle")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dep in self.tasks[task_id].definition.dependencies:
                visit(dep)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in sorted(task_ids):
            visit(task_id)

    def refresh_ready_tasks(self) -> list[str]:
        self.validate_dag()
        newly_ready: list[str] = []
        for task_id, record in self.tasks.items():
            if record.state is not TaskState.PENDING:
                continue
            if all(self.tasks[d].state is TaskState.SUCCEEDED for d in record.definition.dependencies):
                record.transition_to(TaskState.READY)
                newly_ready.append(task_id)
        return newly_ready

    def derived_terminal_state(self) -> JobState | None:
        """Return the job terminal state implied by terminal task states.

        This method is intentionally pure: callers decide when to persist/apply
        the returned state. A mixed SUCCEEDED/CANCELLED job is CANCELLED; any
        failed task makes the completed job FAILED.
        """
        if not self.tasks:
            return JobState.SUCCEEDED

        terminal = {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}
        states = {record.state for record in self.tasks.values()}
        if not states.issubset(terminal):
            return None
        if TaskState.FAILED in states:
            return JobState.FAILED
        if TaskState.CANCELLED in states:
            return JobState.CANCELLED
        return JobState.SUCCEEDED

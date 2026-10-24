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


@dataclass(slots=True)
class JobRecord:
    job_id: str
    priority: int
    tasks: dict[str, TaskRecord]
    state: JobState = JobState.QUEUED

    def validate_dag(self) -> None:
        task_ids = set(self.tasks)
        for record in self.tasks.values():
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

        for task_id in task_ids:
            visit(task_id)

    def refresh_ready_tasks(self) -> list[str]:
        self.validate_dag()
        newly_ready: list[str] = []
        for task_id, record in self.tasks.items():
            if record.state is not TaskState.PENDING:
                continue
            if all(self.tasks[d].state is TaskState.SUCCEEDED for d in record.definition.dependencies):
                record.state = TaskState.READY
                newly_ready.append(task_id)
        return newly_ready

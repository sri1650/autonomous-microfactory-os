from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json

from microfactory.domain.models import JobRecord, JobState, TaskState
from microfactory.domain.repositories import EventSink, JobRepository
from microfactory.domain.transitions import assert_job_transition


@dataclass(frozen=True, slots=True)
class OperationResult:
    job: JobRecord
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class _IdempotencyEntry:
    fingerprint: tuple[str, ...]
    job: JobRecord


class Orchestrator:
    """Framework-independent job/task lifecycle service.

    Idempotency is intentionally local to this service for the first milestone.
    The durable PostgreSQL adapter later persists command identity across restarts.
    """

    def __init__(self, jobs: JobRepository, events: EventSink) -> None:
        self._jobs = jobs
        self._events = events
        self._operations: dict[str, _IdempotencyEntry] = {}

    def submit_job(self, job: JobRecord, *, command_id: str) -> OperationResult:
        definition = {
            "job_id": job.job_id, "priority": job.priority,
            "tasks": [asdict(task.definition) for _, task in sorted(job.tasks.items())],
        }
        encoded = json.dumps(definition, sort_keys=True, separators=(",", ":"), allow_nan=False)
        fingerprint = ("submit", job.job_id, hashlib.sha256(encoded.encode("utf-8")).hexdigest())
        replay = self._replay(command_id, fingerprint)
        if replay is not None:
            return replay

        existing = self._jobs.get(job.job_id)
        if existing is not None:
            if existing == job:
                result = OperationResult(existing, replayed=True)
                self._remember(command_id, fingerprint, existing)
                return result
            raise ValueError(f"job_id {job.job_id!r} already exists with different content")

        working = deepcopy(job)
        working.validate_dag()
        assert_job_transition(working.state, JobState.PLANNING)
        working.state = JobState.PLANNING
        working.refresh_ready_tasks()
        assert_job_transition(working.state, JobState.RUNNING)
        working.state = JobState.RUNNING
        terminal = working.derived_terminal_state()
        if terminal is not None:
            assert_job_transition(working.state, terminal)
            working.state = terminal

        self._jobs.save(working)
        self._events.append(
            event_type="JOB_SUBMITTED",
            aggregate_id=working.job_id,
            payload={"state": working.state.value, "command_id": command_id},
        )
        self._remember(command_id, fingerprint, working)
        return OperationResult(deepcopy(working))

    def transition_task(
        self,
        job_id: str,
        task_id: str,
        target: TaskState,
        *,
        command_id: str,
        resource_id: str | None = None,
    ) -> OperationResult:
        fingerprint = (
            "task_transition",
            job_id,
            task_id,
            target.value,
            resource_id or "",
        )
        replay = self._replay(command_id, fingerprint)
        if replay is not None:
            return replay

        job = self._require_job(job_id)
        try:
            task = job.tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"unknown task {task_id!r}") from exc

        # A terminal task failure can make the job FAILED before an explicit
        # retry decision is made. Permit only FAILED-task -> READY to reopen
        # that job; all other task mutations still require RUNNING.
        if job.state is JobState.FAILED:
            if not (task.state is TaskState.FAILED and target is TaskState.READY):
                raise ValueError(f"job {job_id!r} is not running")
            assert_job_transition(job.state, JobState.RUNNING)
            job.state = JobState.RUNNING
        elif job.state is not JobState.RUNNING:
            raise ValueError(f"job {job_id!r} is not running")

        previous = task.state
        task.transition_to(target)

        if target is TaskState.ASSIGNED:
            if resource_id is None:
                raise ValueError("resource_id is required when assigning a task")
            task.assigned_resource_id = resource_id
        elif target is TaskState.READY and previous is TaskState.FAILED:
            task.attempt += 1
            task.assigned_resource_id = None
        elif target in {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}:
            # Keep the last assigned resource for terminal observability.
            pass

        if target is TaskState.SUCCEEDED:
            job.refresh_ready_tasks()

        terminal = job.derived_terminal_state()
        if terminal is not None:
            assert_job_transition(job.state, terminal)
            job.state = terminal

        self._jobs.save(job)
        self._events.append(
            event_type="TASK_STATE_CHANGED",
            aggregate_id=job.job_id,
            payload={
                "task_id": task_id,
                "from": previous.value,
                "to": target.value,
                "resource_id": resource_id,
                "command_id": command_id,
            },
        )
        self._remember(command_id, fingerprint, job)
        return OperationResult(deepcopy(job))

    def retry_task(self, job_id: str, task_id: str, *, command_id: str) -> OperationResult:
        return self.transition_task(
            job_id,
            task_id,
            TaskState.READY,
            command_id=command_id,
        )

    def cancel_job(self, job_id: str, *, command_id: str) -> OperationResult:
        fingerprint = ("cancel_job", job_id)
        replay = self._replay(command_id, fingerprint)
        if replay is not None:
            return replay

        job = self._require_job(job_id)
        if job.state is JobState.CANCELLED:
            self._remember(command_id, fingerprint, job)
            return OperationResult(deepcopy(job), replayed=True)
        if job.state in {JobState.SUCCEEDED, JobState.FAILED}:
            raise ValueError(f"terminal job {job_id!r} cannot be cancelled")

        for task in job.tasks.values():
            if task.state in {TaskState.SUCCEEDED, TaskState.CANCELLED}:
                continue
            # FAILED -> CANCELLED is intentionally not a legal transition. It
            # remains failed while the job-level cancellation records intent.
            if task.state is TaskState.FAILED:
                continue
            task.transition_to(TaskState.CANCELLED)

        assert_job_transition(job.state, JobState.CANCELLED)
        job.state = JobState.CANCELLED
        self._jobs.save(job)
        self._events.append(
            event_type="JOB_CANCELLED",
            aggregate_id=job.job_id,
            payload={"command_id": command_id},
        )
        self._remember(command_id, fingerprint, job)
        return OperationResult(deepcopy(job))

    def get_job(self, job_id: str) -> JobRecord:
        return deepcopy(self._require_job(job_id))

    def _require_job(self, job_id: str) -> JobRecord:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"unknown job {job_id!r}")
        return job

    def _replay(self, command_id: str, fingerprint: tuple[str, ...]) -> OperationResult | None:
        if not isinstance(command_id, str) or not command_id.strip():
            raise ValueError("command_id must be a non-empty opaque string")
        entry = self._operations.get(command_id)
        if entry is None:
            return None
        if entry.fingerprint != fingerprint:
            raise ValueError(f"command_id {command_id!r} was already used for a different operation")
        return OperationResult(deepcopy(entry.job), replayed=True)

    def _remember(self, command_id: str, fingerprint: tuple[str, ...], job: JobRecord) -> None:
        self._operations[command_id] = _IdempotencyEntry(fingerprint, deepcopy(job))

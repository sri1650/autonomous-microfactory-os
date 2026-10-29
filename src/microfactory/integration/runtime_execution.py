from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import time
from typing import Any, Protocol

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from microfactory.contracts.generated import factory_pb2
from microfactory.domain.models import TaskState
from microfactory.domain.repositories import EventSink
from microfactory.orchestrator import Orchestrator


class CommandJournal(Protocol):
    def record(
        self,
        command_id: str,
        operation_fingerprint: str,
        aggregate_id: str,
        result: dict,
    ) -> dict: ...


class RuntimeTerminal(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"
    SESSION_LOST = "SESSION_LOST"
    RESULT_UNAVAILABLE = "RESULT_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class RuntimeExecutionReceipt:
    job_id: str
    task_id: str
    robot_id: str
    command_id: str
    runtime_session_id: str
    terminal: RuntimeTerminal
    detail: str


class RuntimeExecutionError(RuntimeError):
    """The runtime command could not enter an observable execution lifecycle."""


class RuntimeTaskExecutor:
    """Causal bridge from a MOVE task to a software Rust runtime result.

    An ACCEPTED acknowledgement only moves the task to EXECUTING. The task and
    job become terminal exclusively from GetCommandResult, or conservatively
    fail if the runtime session/result disappears. This adapter deliberately
    supports only the explicit loopback software runtime contract.
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        stub: Any,
        events: EventSink,
        command_journal: CommandJournal,
        *,
        poll_interval_s: float = 0.01,
    ) -> None:
        if poll_interval_s <= 0:
            raise ValueError("poll_interval_s must be positive")
        self._orchestrator = orchestrator
        self._stub = stub
        self._events = events
        self._journal = command_journal
        self._poll_interval_s = poll_interval_s

    def execute_move(
        self,
        *,
        job_id: str,
        task_id: str,
        robot_id: str,
        command_id: str,
        waypoints: list[list[float]],
        step_ms: int = 10,
        fail_after_steps: int | None = None,
        command_timeout_s: float = 5.0,
        result_timeout_s: float = 10.0,
    ) -> RuntimeExecutionReceipt:
        if command_timeout_s <= 0 or result_timeout_s <= 0:
            raise ValueError("timeouts must be positive")
        job = self._orchestrator.get_job(job_id)
        try:
            task = job.tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"unknown task {task_id!r}") from exc
        if task.definition.kind != "MOVE":
            raise ValueError("runtime executor supports MOVE tasks only")
        if task.state not in {TaskState.READY, TaskState.ASSIGNED, TaskState.EXECUTING}:
            raise ValueError(f"task {task_id!r} is not executable from {task.state.value}")

        status = self._status(robot_id)
        if not status.software_simulation:
            raise RuntimeExecutionError("runtime did not declare explicit software simulation mode")
        if not status.runtime_session_id:
            raise RuntimeExecutionError("runtime omitted its session identity")

        payload: dict[str, Any] = {"waypoints": waypoints, "step_ms": step_ms}
        if fail_after_steps is not None:
            payload["fail_after_steps"] = fail_after_steps
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        fingerprint = hashlib.sha256(
            b"\0".join(
                value.encode()
                for value in ("MOVE", job_id, task_id, robot_id)
            )
            + b"\0"
            + encoded
        ).hexdigest()
        intent = {
            "job_id": job_id,
            "task_id": task_id,
            "robot_id": robot_id,
            "runtime_session_id": status.runtime_session_id,
            "payload_sha256": hashlib.sha256(encoded).hexdigest(),
        }
        recorded = self._journal.record(command_id, fingerprint, job_id, intent)
        if {
            key: recorded.get(key)
            for key in ("job_id", "task_id", "robot_id", "payload_sha256")
        } != {
            key: intent[key]
            for key in ("job_id", "task_id", "robot_id", "payload_sha256")
        }:
            raise RuntimeExecutionError("persisted command intent differs from this execution")
        recorded_session = str(recorded.get("runtime_session_id", ""))
        if recorded_session != status.runtime_session_id:
            if task.state is TaskState.ASSIGNED:
                self._orchestrator.transition_task(
                    job_id, task_id, TaskState.EXECUTING,
                    command_id=f"{command_id}:executing-after-restart", resource_id=robot_id,
                )
            if task.state in {TaskState.ASSIGNED, TaskState.EXECUTING}:
                return self._fail_closed(
                    job_id, task_id, robot_id, command_id, recorded_session,
                    RuntimeTerminal.SESSION_LOST,
                    "persisted command belongs to a different runtime session",
                )
            raise RuntimeExecutionError("persisted command belongs to a different runtime session")

        deadline = Timestamp()
        deadline.FromNanoseconds(time.time_ns() + int(command_timeout_s * 1_000_000_000))
        command = factory_pb2.RobotCommand(
            command_id=command_id,
            correlation_id=job_id,
            robot_id=robot_id,
            kind="MOVE",
            deadline=deadline,
            payload_json=encoded,
        )
        try:
            ack = self._stub.SubmitCommand(command, timeout=min(5.0, result_timeout_s))
        except grpc.RpcError as exc:
            raise RuntimeExecutionError(f"runtime submission unavailable: {exc.code().name}") from exc
        if ack.command_id != command_id:
            raise RuntimeExecutionError("runtime acknowledgement changed command identity")
        if ack.disposition != factory_pb2.COMMAND_DISPOSITION_ACCEPTED:
            self._events.append(
                event_type="RUNTIME_COMMAND_REJECTED",
                aggregate_id=job_id,
                payload={"task_id": task_id, "robot_id": robot_id, "command_id": command_id,
                         "runtime_session_id": status.runtime_session_id, "reason": ack.reason},
            )
            raise RuntimeExecutionError(f"runtime rejected command: {ack.reason}")

        if task.state is TaskState.READY:
            self._orchestrator.transition_task(
                job_id, task_id, TaskState.ASSIGNED,
                command_id=f"{command_id}:assigned", resource_id=robot_id,
            )
            task_state = TaskState.ASSIGNED
        else:
            task_state = task.state
        if task_state is TaskState.ASSIGNED:
            self._orchestrator.transition_task(
                job_id, task_id, TaskState.EXECUTING,
                command_id=f"{command_id}:executing", resource_id=robot_id,
            )
        self._events.append(
            event_type="RUNTIME_COMMAND_ACCEPTED",
            aggregate_id=job_id,
            payload={"task_id": task_id, "robot_id": robot_id, "command_id": command_id,
                     "runtime_session_id": status.runtime_session_id},
        )

        query = factory_pb2.CommandResultRequest(robot_id=robot_id, command_id=command_id)
        stop_at = time.monotonic() + result_timeout_s
        while time.monotonic() < stop_at:
            current = self._status_or_failure(job_id, task_id, robot_id, command_id, status.runtime_session_id)
            if current is not None:
                return current
            try:
                result = self._stub.GetCommandResult(query, timeout=min(2.0, result_timeout_s))
            except grpc.RpcError as exc:
                return self._fail_closed(
                    job_id, task_id, robot_id, command_id, status.runtime_session_id,
                    RuntimeTerminal.RESULT_UNAVAILABLE, f"GetCommandResult failed: {exc.code().name}",
                )
            if result.command_id != command_id:
                return self._fail_closed(
                    job_id, task_id, robot_id, command_id, status.runtime_session_id,
                    RuntimeTerminal.RESULT_UNAVAILABLE, "runtime result changed command identity",
                )
            if result.state != factory_pb2.COMMAND_TERMINAL_STATE_UNSPECIFIED:
                return self._consume_terminal(
                    job_id, task_id, robot_id, command_id, status.runtime_session_id,
                    result.state, result.detail,
                )
            time.sleep(self._poll_interval_s)

        try:
            cancelled = self._stub.CancelCommand(query, timeout=2.0)
        except grpc.RpcError as exc:
            return self._fail_closed(
                job_id, task_id, robot_id, command_id, status.runtime_session_id,
                RuntimeTerminal.RESULT_UNAVAILABLE,
                f"result polling expired and cancellation failed: {exc.code().name}",
            )
        return self._consume_terminal(
            job_id, task_id, robot_id, command_id, status.runtime_session_id,
            cancelled.state, cancelled.detail,
        )

    def _status(self, robot_id: str):
        return self._stub.GetStatus(
            factory_pb2.RobotStatusRequest(robot_id=robot_id), timeout=2.0
        )

    def _status_or_failure(
        self, job_id: str, task_id: str, robot_id: str, command_id: str, session_id: str
    ) -> RuntimeExecutionReceipt | None:
        try:
            current = self._status(robot_id)
        except grpc.RpcError as exc:
            return self._fail_closed(
                job_id, task_id, robot_id, command_id, session_id,
                RuntimeTerminal.RESULT_UNAVAILABLE, f"runtime status unavailable: {exc.code().name}",
            )
        if current.runtime_session_id != session_id:
            return self._fail_closed(
                job_id, task_id, robot_id, command_id, session_id,
                RuntimeTerminal.SESSION_LOST, "runtime session changed before terminal result",
            )
        return None

    def _consume_terminal(
        self,
        job_id: str,
        task_id: str,
        robot_id: str,
        command_id: str,
        session_id: str,
        state: int,
        detail: str,
    ) -> RuntimeExecutionReceipt:
        mapping = {
            factory_pb2.COMMAND_TERMINAL_STATE_SUCCEEDED: (RuntimeTerminal.SUCCEEDED, TaskState.SUCCEEDED),
            factory_pb2.COMMAND_TERMINAL_STATE_FAILED: (RuntimeTerminal.FAILED, TaskState.FAILED),
            factory_pb2.COMMAND_TERMINAL_STATE_TIMED_OUT: (RuntimeTerminal.TIMED_OUT, TaskState.FAILED),
            factory_pb2.COMMAND_TERMINAL_STATE_CANCELLED: (RuntimeTerminal.CANCELLED, TaskState.CANCELLED),
        }
        if state not in mapping:
            return self._fail_closed(
                job_id, task_id, robot_id, command_id, session_id,
                RuntimeTerminal.RESULT_UNAVAILABLE, "runtime returned a non-terminal result",
            )
        terminal, task_state = mapping[state]
        self._orchestrator.transition_task(
            job_id, task_id, task_state,
            command_id=f"{command_id}:terminal:{terminal.value}", resource_id=robot_id,
        )
        self._events.append(
            event_type="RUNTIME_COMMAND_TERMINAL",
            aggregate_id=job_id,
            payload={"task_id": task_id, "robot_id": robot_id, "command_id": command_id,
                     "runtime_session_id": session_id, "terminal": terminal.value, "detail": detail},
        )
        return RuntimeExecutionReceipt(
            job_id, task_id, robot_id, command_id, session_id, terminal, detail
        )

    def _fail_closed(
        self,
        job_id: str,
        task_id: str,
        robot_id: str,
        command_id: str,
        session_id: str,
        terminal: RuntimeTerminal,
        detail: str,
    ) -> RuntimeExecutionReceipt:
        job = self._orchestrator.get_job(job_id)
        if job.tasks[task_id].state is TaskState.EXECUTING:
            self._orchestrator.transition_task(
                job_id, task_id, TaskState.FAILED,
                command_id=f"{command_id}:terminal:{terminal.value}", resource_id=robot_id,
            )
        self._events.append(
            event_type="RUNTIME_COMMAND_TERMINAL",
            aggregate_id=job_id,
            payload={"task_id": task_id, "robot_id": robot_id, "command_id": command_id,
                     "runtime_session_id": session_id, "terminal": terminal.value, "detail": detail},
        )
        return RuntimeExecutionReceipt(
            job_id, task_id, robot_id, command_id, session_id, terminal, detail
        )


from __future__ import annotations

from dataclasses import dataclass, field

from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.contracts.generated import factory_pb2
from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord, TaskState
from microfactory.integration import RuntimeExecutionError, RuntimeTaskExecutor, RuntimeTerminal
from microfactory.orchestrator import Orchestrator


@dataclass
class Journal:
    values: dict[str, tuple[str, str, dict]] = field(default_factory=dict)

    def record(self, command_id, operation_fingerprint, aggregate_id, result):
        value = (operation_fingerprint, aggregate_id, dict(result))
        existing = self.values.setdefault(command_id, value)
        if existing[:2] != value[:2]:
            raise ValueError("command_id was reused for a different operation")
        return dict(existing[2])


class Stub:
    def __init__(self, orchestrator, *, terminal=None, accepted=True, change_session=False):
        self.orchestrator = orchestrator
        self.terminal = terminal or factory_pb2.COMMAND_TERMINAL_STATE_SUCCEEDED
        self.accepted = accepted
        self.change_session = change_session
        self.result_calls = 0

    def GetStatus(self, request, timeout):
        session = "session-2" if self.change_session and self.result_calls else "session-1"
        return factory_pb2.RobotStatus(
            robot_id=request.robot_id, runtime_session_id=session, software_simulation=True,
        )

    def SubmitCommand(self, command, timeout):
        disposition = (factory_pb2.COMMAND_DISPOSITION_ACCEPTED if self.accepted
                       else factory_pb2.COMMAND_DISPOSITION_REJECTED)
        return factory_pb2.CommandAck(
            command_id=command.command_id, disposition=disposition, reason="busy" if not self.accepted else "",
        )

    def GetCommandResult(self, request, timeout):
        self.result_calls += 1
        if self.result_calls == 1:
            job = self.orchestrator.get_job("job-1")
            assert job.state is JobState.RUNNING
            assert job.tasks["move"].state is TaskState.EXECUTING
            return factory_pb2.CommandResult(
                command_id=request.command_id,
                state=factory_pb2.COMMAND_TERMINAL_STATE_UNSPECIFIED,
                detail="pending",
            )
        return factory_pb2.CommandResult(
            command_id=request.command_id, state=self.terminal, detail="runtime-authored",
        )

    def CancelCommand(self, request, timeout):
        return factory_pb2.CommandResult(
            command_id=request.command_id,
            state=factory_pb2.COMMAND_TERMINAL_STATE_CANCELLED,
            detail="cancelled",
        )


class CrashAfterAcceptanceStub(Stub):
    def GetCommandResult(self, request, timeout):
        raise KeyboardInterrupt("simulated orchestrator process loss")


class NewSessionStub(Stub):
    def GetStatus(self, request, timeout):
        return factory_pb2.RobotStatus(
            robot_id=request.robot_id, runtime_session_id="session-restarted",
            software_simulation=True,
        )


def setup():
    jobs = InMemoryJobRepository(); events = InMemoryEventSink()
    orchestrator = Orchestrator(jobs, events)
    orchestrator.submit_job(
        JobRecord("job-1", 1, {"move": TaskRecord(TaskDefinition("move", "MOVE", "mover"))}),
        command_id="submit",
    )
    return orchestrator, events


def execute(orchestrator, events, stub, journal=None):
    return RuntimeTaskExecutor(
        orchestrator, stub, events, journal or Journal(), poll_interval_s=0.0001,
    ).execute_move(
        job_id="job-1", task_id="move", robot_id="robot-1", command_id="move-1",
        waypoints=[[0, 0], [1, 0]], step_ms=1,
    )


def test_accepted_is_not_completed_before_terminal_result():
    orchestrator, events = setup(); stub = Stub(orchestrator)
    receipt = execute(orchestrator, events, stub)
    assert stub.result_calls == 2
    assert receipt.terminal is RuntimeTerminal.SUCCEEDED
    assert orchestrator.get_job("job-1").state is JobState.SUCCEEDED


def test_runtime_failure_persists_failed_task_and_job():
    orchestrator, events = setup()
    receipt = execute(
        orchestrator, events,
        Stub(orchestrator, terminal=factory_pb2.COMMAND_TERMINAL_STATE_FAILED),
    )
    assert receipt.terminal is RuntimeTerminal.FAILED
    job = orchestrator.get_job("job-1")
    assert job.tasks["move"].state is TaskState.FAILED
    assert job.state is JobState.FAILED


def test_changed_runtime_session_fails_closed_without_success():
    orchestrator, events = setup()
    receipt = execute(orchestrator, events, Stub(orchestrator, change_session=True))
    assert receipt.terminal is RuntimeTerminal.SESSION_LOST
    assert orchestrator.get_job("job-1").state is JobState.FAILED


def test_rejected_command_does_not_enter_executing_or_success():
    orchestrator, events = setup()
    try:
        execute(orchestrator, events, Stub(orchestrator, accepted=False))
    except RuntimeExecutionError as exc:
        assert "rejected" in str(exc)
    else:
        raise AssertionError("rejected command unexpectedly executed")
    job = orchestrator.get_job("job-1")
    assert job.state is JobState.RUNNING
    assert job.tasks["move"].state is TaskState.READY


def test_command_identity_conflict_is_rejected_before_resubmission():
    orchestrator, events = setup(); journal = Journal(); stub = Stub(orchestrator)
    execute(orchestrator, events, stub, journal)
    # A fresh job with the same external command identity but different payload
    # cannot reuse the durable operation identity.
    orchestrator, events = setup(); stub = Stub(orchestrator)
    executor = RuntimeTaskExecutor(orchestrator, stub, events, journal, poll_interval_s=0.0001)
    try:
        executor.execute_move(
            job_id="job-1", task_id="move", robot_id="robot-1", command_id="move-1",
            waypoints=[[0, 0], [0, 1]], step_ms=1,
        )
    except ValueError as exc:
        assert "different operation" in str(exc)
    else:
        raise AssertionError("conflicting command identity unexpectedly replayed")


def test_orchestrator_restart_with_changed_runtime_session_fails_persisted_execution():
    orchestrator, events = setup(); journal = Journal()
    try:
        execute(orchestrator, events, CrashAfterAcceptanceStub(orchestrator), journal)
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("simulated process loss did not interrupt polling")
    assert orchestrator.get_job("job-1").tasks["move"].state is TaskState.EXECUTING

    receipt = execute(orchestrator, events, NewSessionStub(orchestrator), journal)
    assert receipt.terminal is RuntimeTerminal.SESSION_LOST
    assert orchestrator.get_job("job-1").state is JobState.FAILED


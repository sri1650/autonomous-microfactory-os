from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import socket
import subprocess

from fastapi.testclient import TestClient
import grpc
import psycopg
import pytest

from apps.factory_api import create_app
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.adapters.postgres import (
    PostgresCommandRepository,
    PostgresEventStore,
    PostgresJobRepository,
)
from microfactory.contracts.generated import factory_pb2_grpc
from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord
from microfactory.integration import RuntimeTaskExecutor, RuntimeTerminal
from microfactory.orchestrator import Orchestrator


ROOT = Path(__file__).parents[2]


@dataclass
class MemoryCommandJournal:
    records: dict[str, tuple[str, str, dict]] = field(default_factory=dict)

    def record(self, command_id, operation_fingerprint, aggregate_id, result):
        candidate = (operation_fingerprint, aggregate_id, dict(result))
        previous = self.records.setdefault(command_id, candidate)
        if previous[:2] != candidate[:2]:
            raise ValueError("command_id was reused for a different operation")
        return dict(previous[2])


def _port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _job(job_id: str) -> JobRecord:
    return JobRecord(
        job_id, 10,
        {"move": TaskRecord(TaskDefinition("move", "MOVE", "mover"))},
    )


def _runtime(robot_id: str):
    port = _port()
    process = subprocess.Popen(
        ["cargo", "run", "--quiet", "-p", "robot_runtime", "--bin",
         "robot_runtime_server", "--", f"127.0.0.1:{port}", robot_id,
         "--simulate", "0", "0"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    assert process.stdout is not None
    assert process.stdout.readline().startswith("READY ")
    channel = grpc.insecure_channel(f"127.0.0.1:{port}")
    grpc.channel_ready_future(channel).result(timeout=10)
    return process, channel, factory_pb2_grpc.RobotRuntimeStub(channel)


def test_actual_rust_terminal_result_drives_orchestrator_and_live_api():
    jobs = InMemoryJobRepository(); events = InMemoryEventSink()
    orchestrator = Orchestrator(jobs, events)
    orchestrator.submit_job(_job("job-causal-memory"), command_id="submit-memory")
    process, channel, stub = _runtime("robot-memory")
    try:
        receipt = RuntimeTaskExecutor(
            orchestrator, stub, events, MemoryCommandJournal()
        ).execute_move(
            job_id="job-causal-memory", task_id="move", robot_id="robot-memory",
            command_id="move-memory", waypoints=[[0, 0], [1, 0], [1, 1]], step_ms=5,
        )
        assert receipt.terminal is RuntimeTerminal.SUCCEEDED
        response = TestClient(create_app(orchestrator)).get("/jobs/job-causal-memory")
        assert response.status_code == 200
        assert response.json()["state"] == JobState.SUCCEEDED.value
        terminal = [event for event in events.events if event.event_type == "RUNTIME_COMMAND_TERMINAL"]
        assert terminal and terminal[-1].payload["terminal"] == "SUCCEEDED"
    finally:
        channel.close(); process.terminate(); process.wait(timeout=10)


def test_actual_terminal_result_is_durable_and_replayed_by_live_api():
    dsn = os.environ.get("MICROFACTORY_POSTGRES_DSN")
    if not dsn:
        pytest.skip("set MICROFACTORY_POSTGRES_DSN for causal persistence acceptance")
    migration = (ROOT / "db/migrations/001_init.sql").read_text()
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(migration)
        connection.execute(
            "TRUNCATE command_idempotency, domain_events, tasks, resources, jobs CASCADE"
        )
    jobs = PostgresJobRepository.from_dsn(dsn)
    events = PostgresEventStore.from_dsn(dsn)
    journal = PostgresCommandRepository.from_dsn(dsn)
    orchestrator = Orchestrator(jobs, events)
    orchestrator.submit_job(_job("job-causal-postgres"), command_id="submit-postgres")
    process, channel, stub = _runtime("robot-postgres")
    try:
        receipt = RuntimeTaskExecutor(orchestrator, stub, events, journal).execute_move(
            job_id="job-causal-postgres", task_id="move", robot_id="robot-postgres",
            command_id="move-postgres", waypoints=[[0, 0], [1, 0], [2, 0]], step_ms=5,
        )
        assert receipt.terminal is RuntimeTerminal.SUCCEEDED
    finally:
        channel.close(); process.terminate(); process.wait(timeout=10)

    restarted = Orchestrator(PostgresJobRepository.from_dsn(dsn), PostgresEventStore.from_dsn(dsn))
    client = TestClient(create_app(restarted, event_reader=PostgresEventStore.from_dsn(dsn)))
    job_response = client.get("/jobs/job-causal-postgres")
    assert job_response.status_code == 200
    assert job_response.json()["state"] == JobState.SUCCEEDED.value
    event_response = client.get("/jobs/job-causal-postgres/events")
    assert event_response.status_code == 200
    events_payload = event_response.json()["events"]
    types = [event["event_type"] for event in events_payload]
    assert "RUNTIME_COMMAND_ACCEPTED" in types
    assert "RUNTIME_COMMAND_TERMINAL" in types
    terminal = next(event for event in reversed(events_payload)
                    if event["event_type"] == "RUNTIME_COMMAND_TERMINAL")
    assert terminal["payload"]["terminal"] == "SUCCEEDED"
    assert json.loads(receipt.detail)["runtime_session_id"] == receipt.runtime_session_id


from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess

import clickhouse_connect
import grpc
from opentelemetry.sdk.trace import TracerProvider
import psycopg
import pytest

from microfactory.adapters.postgres import PostgresJobRepository
from microfactory.contracts.generated import factory_pb2, factory_pb2_grpc
from microfactory.domain.models import JobRecord, JobState, ResourceRecord, TaskDefinition, TaskRecord
from microfactory.integration import run_python_vertical_slice
from microfactory.replay import persisted_record_digest, replay_persisted_records
from microfactory.scheduler.cp_sat import build_problem, solve_cp_sat
from microfactory.telemetry import ClickHouseTelemetrySink, TelemetryRecord
from microfactory.telemetry.tracing import inject_trace_context


ROOT = Path(__file__).parents[2]


def _port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _planning_job(job_id: str, priority: int) -> JobRecord:
    move = f"{job_id}-move"
    inspect = f"{job_id}-inspect"
    return JobRecord(
        job_id,
        priority,
        {
            move: TaskRecord(TaskDefinition(move, "MOVE", "mover", payload={"duration": 3})),
            inspect: TaskRecord(
                TaskDefinition(inspect, "INSPECT", "vision", dependencies=(move,), payload={"duration": 1})
            ),
        },
    )


def test_three_job_live_full_stack_golden_scenario():
    dsn = os.environ.get("MICROFACTORY_POSTGRES_DSN")
    clickhouse_host = os.environ.get("MICROFACTORY_CLICKHOUSE_HOST")
    if not dsn or not clickhouse_host:
        pytest.skip("live PostgreSQL and ClickHouse settings are required")

    expected = json.loads((ROOT / "scenarios/e2e/full_stack_golden.json").read_text())
    migration = (ROOT / "db/migrations/001_init.sql").read_text()
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(migration)
        connection.execute("TRUNCATE command_idempotency, domain_events, tasks, resources, jobs CASCADE")

    clickhouse_settings = {
        "host": clickhouse_host,
        "port": int(os.environ.get("MICROFACTORY_CLICKHOUSE_PORT", "8123")),
        "database": os.environ.get("MICROFACTORY_CLICKHOUSE_DATABASE", "microfactory"),
        "username": os.environ.get("MICROFACTORY_CLICKHOUSE_USER", "default"),
        "password": os.environ.get("MICROFACTORY_CLICKHOUSE_PASSWORD", ""),
    }
    clickhouse = clickhouse_connect.get_client(**clickhouse_settings)
    clickhouse.command((ROOT / "telemetry/clickhouse/001_events.sql").read_text())
    clickhouse.command("TRUNCATE TABLE robotics_events")

    slice_result = run_python_vertical_slice(ROOT / "scenarios/e2e/python_vertical_slice.json")
    assert sorted(slice_result.jobs) == sorted(expected["jobs"])
    assert all(job.state is JobState.SUCCEEDED for job in slice_result.jobs.values())

    planning_jobs = [_planning_job(job_id, 30 - index * 10) for index, job_id in enumerate(expected["jobs"])]
    schedule = solve_cp_sat(
        build_problem(
            planning_jobs,
            [
                *(ResourceRecord(robot, "mover") for robot in expected["robots"]),
                ResourceRecord("vision-1", "vision"),
            ],
        )
    )
    assert schedule.optimal
    assert schedule.makespan == expected["expected_scheduler_makespan"]

    repository = PostgresJobRepository.from_dsn(dsn)
    for job in slice_result.jobs.values():
        repository.save(job)
    assert all(repository.get(job_id).state is JobState.SUCCEEDED for job_id in expected["jobs"])

    processes: list[subprocess.Popen[str]] = []
    channels: list[grpc.Channel] = []
    sink = ClickHouseTelemetrySink.connect(**clickhouse_settings)
    try:
        provider = TracerProvider()
        tracer = provider.get_tracer("microfactory-e2e")
        for sequence, (job_id, robot_id) in enumerate(zip(expected["jobs"], expected["robots"], strict=True), 1):
            port = _port()
            process = subprocess.Popen(
                ["cargo", "run", "--quiet", "-p", "robot_runtime", "--bin", "robot_runtime_server", "--", f"127.0.0.1:{port}", robot_id],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            processes.append(process)
            assert process.stdout is not None and process.stdout.readline().startswith("READY ")
            channel = grpc.insecure_channel(f"127.0.0.1:{port}")
            channels.append(channel)
            grpc.channel_ready_future(channel).result(timeout=10)
            stub = factory_pb2_grpc.RobotRuntimeStub(channel)
            with tracer.start_as_current_span(f"submit:{job_id}"):
                ack, call = stub.SubmitCommand.with_call(
                    factory_pb2.RobotCommand(command_id=f"move:{job_id}", correlation_id=job_id, robot_id=robot_id, kind="MOVE"),
                    metadata=tuple(inject_trace_context().items()),
                    timeout=10,
                )
            assert ack.disposition == factory_pb2.COMMAND_DISPOSITION_ACCEPTED
            metadata = dict(call.initial_metadata())
            trace_id = metadata["x-microfactory-trace-id"]
            span_id = metadata["x-microfactory-span-id"]
            records = [
                TelemetryRecord(sequence * 100, "JOB_SUBMITTED", job_id, job_id, trace_id, span_id, {"state": "RUNNING"}),
                TelemetryRecord(sequence * 100 + 1, "RUNTIME_ACCEPTED", robot_id, job_id, trace_id, span_id, {"state": "ACCEPTED"}),
                TelemetryRecord(sequence * 100 + 2, "TASK_STATE_CHANGED", job_id, job_id, trace_id, span_id, {"task_id": f"{job_id}-move", "to": "SUCCEEDED"}),
                TelemetryRecord(sequence * 100 + 3, "VISION_VERIFICATION", job_id, job_id, trace_id, span_id, {"decision": "PASS"}),
            ]
            sink.write(records)
            persisted = sink.query_correlation(job_id)
            replay = replay_persisted_records(persisted, expected_digest=persisted_record_digest(persisted))
            assert replay.aggregate_states[job_id] == "PASS"
            assert replay.record_count == 4
    finally:
        for channel in channels:
            channel.close()
        for process in processes:
            process.terminate()
            process.wait(timeout=10)

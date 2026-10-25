from __future__ import annotations

import os
import subprocess
import time

import psycopg
import pytest

from microfactory.adapters.postgres import PostgresCommandRepository, PostgresJobRepository
from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord, TaskState


def job(state: JobState = JobState.RUNNING) -> JobRecord:
    return JobRecord(
        "job-live-1",
        5,
        {
            "move": TaskRecord(
                TaskDefinition("move", "MOVE", "mover", payload={"duration": 3}),
                state=TaskState.READY,
            )
        },
        state,
    )


def test_job_survives_new_repository_connection(postgres_dsn: str):
    PostgresJobRepository.from_dsn(postgres_dsn).save(job())

    restarted_repository = PostgresJobRepository.from_dsn(postgres_dsn)
    assert restarted_repository.get("job-live-1") == job()


def test_transactional_state_update_is_visible_after_restart(postgres_dsn: str):
    repository = PostgresJobRepository.from_dsn(postgres_dsn)
    repository.save(job())
    repository.save(job(JobState.FAILED))

    persisted = PostgresJobRepository.from_dsn(postgres_dsn).get("job-live-1")
    assert persisted is not None
    assert persisted.state is JobState.FAILED


def test_command_idempotency_survives_connections(postgres_dsn: str):
    first = PostgresCommandRepository.from_dsn(postgres_dsn)
    result = first.record("cmd-1", "submit:v1", "job-live-1", {"job_id": "job-live-1"})
    replay = PostgresCommandRepository.from_dsn(postgres_dsn).record(
        "cmd-1", "submit:v1", "job-live-1", {"ignored": True}
    )

    assert result == {"job_id": "job-live-1"}
    assert replay == result
    with pytest.raises(ValueError, match="different operation"):
        PostgresCommandRepository.from_dsn(postgres_dsn).record(
            "cmd-1", "cancel:v1", "job-live-1", {"cancelled": True}
        )


def test_job_survives_postgres_container_restart(postgres_dsn: str):
    container = os.environ.get("MICROFACTORY_POSTGRES_CONTAINER")
    if not container:
        pytest.skip("set MICROFACTORY_POSTGRES_CONTAINER for container restart validation")
    PostgresJobRepository.from_dsn(postgres_dsn).save(job())

    subprocess.run(["docker", "restart", container], check=True, capture_output=True, text=True)
    deadline = time.monotonic() + 30
    while True:
        try:
            with psycopg.connect(postgres_dsn):
                break
        except psycopg.OperationalError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.25)

    assert PostgresJobRepository.from_dsn(postgres_dsn).get("job-live-1") == job()

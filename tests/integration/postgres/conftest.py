from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def postgres_dsn() -> str:
    dsn = os.environ.get("MICROFACTORY_POSTGRES_DSN")
    if not dsn:
        pytest.skip("set MICROFACTORY_POSTGRES_DSN for live PostgreSQL tests")
    migration = (ROOT / "db" / "migrations" / "001_init.sql").read_text(encoding="utf-8")
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(migration)
    return dsn


@pytest.fixture(autouse=True)
def clean_database(postgres_dsn: str):
    with psycopg.connect(postgres_dsn, autocommit=True) as connection:
        connection.execute(
            "TRUNCATE command_idempotency, domain_events, tasks, resources, jobs RESTART IDENTITY CASCADE"
        )
    yield

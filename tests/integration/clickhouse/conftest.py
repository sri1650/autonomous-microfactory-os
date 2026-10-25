from __future__ import annotations

import os
from pathlib import Path

import clickhouse_connect
import pytest


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def clickhouse_settings():
    host = os.environ.get("MICROFACTORY_CLICKHOUSE_HOST")
    if not host:
        pytest.skip("set MICROFACTORY_CLICKHOUSE_HOST for live ClickHouse tests")
    settings = {
        "host": host,
        "port": int(os.environ.get("MICROFACTORY_CLICKHOUSE_PORT", "8123")),
        "database": os.environ.get("MICROFACTORY_CLICKHOUSE_DATABASE", "microfactory"),
        "username": os.environ.get("MICROFACTORY_CLICKHOUSE_USER", "default"),
        "password": os.environ.get("MICROFACTORY_CLICKHOUSE_PASSWORD", ""),
    }
    client = clickhouse_connect.get_client(**settings)
    ddl = (ROOT / "telemetry" / "clickhouse" / "001_events.sql").read_text(encoding="utf-8")
    client.command(ddl)
    return settings


@pytest.fixture(autouse=True)
def clean_clickhouse(clickhouse_settings):
    client = clickhouse_connect.get_client(**clickhouse_settings)
    client.command("TRUNCATE TABLE robotics_events")
    yield

# Demo Capture Checklist

## One-time setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cargo build --workspace
docker run --name microfactory-postgres-test -e POSTGRES_PASSWORD=microfactory -e POSTGRES_DB=microfactory -p 55432:5432 -d postgres:17-alpine
docker run --name microfactory-clickhouse-test -e CLICKHOUSE_PASSWORD=microfactory -e CLICKHOUSE_DB=microfactory -p 58123:8123 -d clickhouse/clickhouse-server:25.8-alpine
```

If the named containers already exist, use `docker start microfactory-postgres-test microfactory-clickhouse-test` instead of creating them again.

## Generate the two browser-ready preview screens

```bash
.venv/bin/python -c "from pathlib import Path; from apps.factory_api.dashboard import dashboard_html; Path('/tmp/microfactory-dashboard.html').write_text(dashboard_html())"
.venv/bin/python -c "from pathlib import Path; from apps.factory_api.time_machine import time_machine_html; Path('/tmp/microfactory-replay.html').write_text(time_machine_html())"
open /tmp/microfactory-dashboard.html
open /tmp/microfactory-replay.html
```

On Linux, replace `open` with `xdg-open`.

## Exact live E2E command

```bash
MICROFACTORY_POSTGRES_DSN=postgresql://postgres:microfactory@127.0.0.1:55432/microfactory \
MICROFACTORY_CLICKHOUSE_HOST=127.0.0.1 \
MICROFACTORY_CLICKHOUSE_PORT=58123 \
MICROFACTORY_CLICKHOUSE_DATABASE=microfactory \
MICROFACTORY_CLICKHOUSE_PASSWORD=microfactory \
.venv/bin/python -m pytest -q tests/e2e -vv
```

Expected: four E2E tests pass. Capture the command and final summary in one frame.

## Exact focused failure command

```bash
.venv/bin/python -m pytest -q tests/e2e/test_failure_recovery.py -vv
```

Expected: one test passes. Explain the blocked aisle, heartbeat timeout and one-attempt vision recovery from the test name and source; do not imply a physical fault was injected.

## Evidence/report command

```bash
.venv/bin/python benchmarks/report.py
sed -n '1,220p' docs/generated/performance_report.md
```

## Screens to capture

- README architecture diagram and scope notice
- terminal with `4 passed` E2E result
- dashboard with “SIMULATION PREVIEW” visible
- time-machine failed and recovered vision frames
- scheduler/fleet/runtime tables in the final report
- final README scope statement

## Recording quality gate

- Hide tokens, passwords beyond the disposable local values above, personal paths and unrelated browser tabs.
- Keep commands and results readable at 1080p.
- Say “simulated”, “local integration test” and “retained benchmark” where applicable.
- Do not claim hardware validation, deployment readiness, production throughput or safety certification.
- Stop or remove the disposable containers after recording if they are no longer needed.

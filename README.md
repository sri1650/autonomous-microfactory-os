# Autonomous Microfactory OS

A deterministic robotics/factory orchestration portfolio project: Python owns jobs, scheduling, fleet planning, vision policy, persistence, telemetry and replay; a Rust/Tonic runtime owns the low-level robot command boundary.

The project is locally verified with **153 Python tests** and **11 Rust tests**. Its golden scenario drives three concurrent jobs through CP-SAT scheduling, conflict-free mover routing, simulated vision, PostgreSQL persistence, three real Rust gRPC processes, ClickHouse telemetry and digest-checked replay.

> Scope: all evidence is local software, synthetic vision or simulation. This repository does not claim physical hardware validation, production deployment, production-scale load, functional-safety certification or safe control of real machinery.

## What is implemented

- Typed job/task/resource lifecycle with DAG validation, legal transitions and idempotent commands
- Deterministic OR-Tools CP-SAT scheduler plus FIFO, priority, SPT, EDD and weighted baselines
- A*, time-expanded A*, reservations, cooperative planning and CBS reference/escalation
- Robot health, battery eligibility, heartbeat watchdog and bounded failure recovery
- Rust/Tonic gRPC command runtime with accepted/rejected/terminal lifecycle and idempotency
- PostgreSQL job persistence and command identity that survive process/database restart
- Python-to-Rust W3C trace propagation and ClickHouse correlation timelines
- OpenCV alignment, PASS/RETRY/FAIL/HUMAN_REVIEW policy and lazy ONNX boundary
- Deterministic simulation, canonical event digests, first-divergence diagnosis and persisted cross-service replay
- Golden and failure E2E scenarios, dashboard preview and replay/time-machine preview

## Architecture

```mermaid
flowchart LR
    API[Factory API / Dashboard] --> O[Python Orchestrator]
    O --> S[CP-SAT / Heuristics]
    O --> F[Cooperative Fleet Planner]
    O --> P[(PostgreSQL)]
    F --> R[Rust gRPC Robot Runtimes]
    R --> SIM[Deterministic Simulator]
    V[Vision Verification] --> O
    O --> T[W3C OpenTelemetry]
    R --> T
    T --> C[(ClickHouse)]
    C --> RP[Persisted Replay / Time Machine]
```

The split is intentional: Python keeps optimisation and integration iteration fast, while Rust isolates the command/watchdog boundary behind a typed protobuf contract.

## Measured evidence

All figures are retained in [the final performance report](docs/generated/performance_report.md) and its adjacent CSV files.

- Scheduler: every strategy reached a 39-tick makespan on the retained workload. CP-SAT weighted tardiness was **227**, versus **229** for the best heuristic (EDD); recorded CP-SAT compute time was **58.647 ms**.
- Fleet: every retained multi-seed run through 100 simulated robots was conflict-free. p50 planning time ranged from **6.13 ms** at 10 robots to **1519.02 ms** at 100 robots.
- Rust runtime, local loopback/100 samples: idempotent `SubmitCommand` p50/p95 **0.193/0.414 ms**; `GetStatus` **0.176/0.331 ms**.
- Synthetic vision, 200 samples: mean latency **0.4531 ms**, mean position error **0.4570 px**, mean angle error **0.1396°**.

These numbers describe this development machine and workload, not an SLA.

## Quick start

Requirements: Python 3.12+, Rust stable and Docker.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest -q
cargo test --workspace
```

Run the deterministic software demo and regenerate the report:

```bash
.venv/bin/python tools/microfactory.py validate-job scenarios/jobs/pcb_batch_104.yaml
.venv/bin/python tools/microfactory.py stress --robots 50 --grid 40 --seed 3
.venv/bin/python benchmarks/scheduler/run.py --output docs/generated/scheduler_comparison.csv
.venv/bin/python benchmarks/report.py
```

## Live integration and E2E

Start disposable local databases:

```bash
docker run --name microfactory-postgres-test -e POSTGRES_PASSWORD=microfactory -e POSTGRES_DB=microfactory -p 55432:5432 -d postgres:17-alpine
docker run --name microfactory-clickhouse-test -e CLICKHOUSE_PASSWORD=microfactory -e CLICKHOUSE_DB=microfactory -p 58123:8123 -d clickhouse/clickhouse-server:25.8-alpine
```

Then run the live suites:

```bash
MICROFACTORY_POSTGRES_DSN=postgresql://postgres:microfactory@127.0.0.1:55432/microfactory \
MICROFACTORY_CLICKHOUSE_HOST=127.0.0.1 \
MICROFACTORY_CLICKHOUSE_PORT=58123 \
MICROFACTORY_CLICKHOUSE_DATABASE=microfactory \
MICROFACTORY_CLICKHOUSE_PASSWORD=microfactory \
.venv/bin/python -m pytest -q tests/integration tests/e2e
```

The migrations/table DDL are applied by the live test fixtures. The golden E2E starts three Rust runtimes on ephemeral loopback ports; the failure scenario proves blocked-aisle replanning, heartbeat-loss rejection and a one-retry vision recovery.

## Repository guide

- `src/microfactory/` — domain, orchestration, scheduling, fleet, vision, telemetry and replay
- `rust/robot_runtime/` — Tonic runtime and watchdog
- `contracts/proto/` — shared protobuf source
- `db/migrations/` and `telemetry/clickhouse/` — live persistence schemas
- `scenarios/` — deterministic jobs, simulations, benchmarks and E2E inputs
- `tests/integration/` and `tests/e2e/` — real-boundary verification
- `docs/generated/` — retained benchmark evidence
- `docs/demo_checklist.md` — exact three-minute demo sequence
- `docs/interview/` — architecture trade-offs, algorithms, failures and limitations

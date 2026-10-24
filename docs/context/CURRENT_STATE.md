# Current State

## Verification baseline

- Python test suite: **140 passing tests**
- Formal task graph: **29/43 complete**
- Formal tasks remaining: M3-T04, M3-T05, M5-T02, M5-T03, M7-T01, M7-T02, M7-T03, M7-T04, M9-T01, M9-T02, M9-T03, M10-T01, M10-T02, M10-T03
- Pre-Codex quality gate: passing
- Fleet retained multi-seed benchmark: conflict-free through 100 robots
- Hardware validation: none claimed

## Completed and verified before Codex

### Domain / orchestration
- typed job/task/resource models
- DAG validation and dependency readiness
- explicit legal task/job transitions
- idempotent command handling
- failed final-task explicit retry path
- FastAPI job/cancel/retry APIs
- health and capability endpoints

### Factory specification / developer UX
- YAML manufacturing job DSL
- example PCB workflow
- CLI for job validation, fleet stress and fault schedules
- one-command pre-Codex quality gate

### Scheduling
- FIFO baseline
- deterministic priority/SPT/EDD/weighted heuristics
- retained scheduler benchmark workload and measured CSV
- CP-SAT problem extraction/data model is prepared and tested
- actual OR-Tools solve implementation intentionally remains for M5-T02

### Fleet
- A*
- time-expanded A*
- reservations
- cooperative/prioritised multi-robot planning
- CBS reference/escalation planner
- persistent goal-cell occupancy safety
- 100-seed invariant testing
- robot health assessment
- battery-aware mission acceptance
- deterministic stress generation
- multi-seed measured scaling through 100 robots

### Simulation / replay
- logical deterministic clock
- factory world
- seeded machine simulation
- immutable events/digests
- deterministic replay
- first-divergence debugger
- replay timeline model
- dashboard and time-machine simulation-preview UIs

### Vision
- typed contracts
- OpenCV alignment
- verification policy PASS/RETRY/FAIL/HUMAN_REVIEW
- lazy ONNX adapter
- synthetic benchmark

### Reliability / fault injection
- deterministic chaos/fault schedules
- robot-health impact model
- frozen diagnostic-agent fault corpus
- guardrails and evaluation harness

### Persistence / observability preparation
- versioned PostgreSQL migration
- PostgreSQL job codec + dependency-injected repository boundary
- Python OpenTelemetry event correlation
- W3C trace-context injection/extraction helpers for future RPC boundary
- ClickHouse DDL + injectable sink boundary

These boundaries are unit-tested but their **live external integrations are not complete**.

### Pre-integration E2E
- three-job Python vertical slice
- scheduling -> fleet routing -> vision -> terminal success
- failure/retry vertical slice
- benchmark/report generation

## Measured local evidence

See:
- `docs/generated/pre_codex_benchmarks.md`
- `docs/generated/fleet_multiseed_100.csv`
- `docs/generated/scheduler_baselines.csv`
- `docs/generated/pre_codex_gate.json`

These are local software/simulation measurements only.

## Deliberately reserved for Codex / Work

Do not spend time redesigning completed Python modules.

1. M3-T04..M3-T05 — protobuf/gRPC service
2. M5-T02 — actual OR-Tools CP-SAT solve implementation
3. M5-T03 — final FIFO/heuristic/CP-SAT benchmark comparison
4. M7-T01 — live psycopg/PostgreSQL container integration, restart/idempotency validation
5. M7-T02 — Rust/gRPC trace-context propagation and full integration trace tests
6. M7-T03 — live ClickHouse server/client integration and queries
7. M7-T04 — persisted cross-service deterministic replay
8. M9-T01..M9-T03 — final full-stack golden/failure E2E + final performance report
9. M10-T01..M10-T03 — final recruiter README/demo/interview pack after integrated evidence exists

## First command in Work

```bash
python tools/pre_codex_gate.py
```

If that passes, start the first dependency-ready incomplete formal task. Do not refactor passing pre-Codex work without a failing deterministic check.

## Codex milestones

- M3-T01 complete: Rust state-machine scaffold is formatted and passes workspace check, Clippy with warnings denied, and 2 Rust tests.
- M3-T02 complete: typed accepted/rejected and terminal command lifecycle with duplicate-command idempotency passes 5 Rust tests and strict Clippy.
- M3-T03 complete: monotonic heartbeat watchdog has deterministic healthy/expired boundary behavior and passes 8 Rust tests with strict Clippy.

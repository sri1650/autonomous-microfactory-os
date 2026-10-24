# Current State

## Completed without Codex/Work usage
- project scope, architecture and Python/Rust responsibility split locked
- Protobuf direction; PostgreSQL/ClickHouse/OpenTelemetry responsibilities decided
- low-credit agent policy and 43-task bounded task graph created
- `M1-T01..T05`: domain DAG/state hardening, repository protocols, in-memory repositories, orchestrator and FastAPI boundary
- `M2-T01..T05`: logical clock/events, deterministic factory world, seeded machines, versioned scenario loader and event-digest determinism
- `M4-T01..T07`: A*, temporal reservations, time-expanded planning, prioritised cooperative planning, adversarial scenarios, benchmark harness and CBS evaluation
- cooperative planner goal occupancy hardened: goal cells remain reserved through the planning horizon
- `M5-T01`: priority/FIFO resource scheduler baseline
- `M6-T01..T05`: vision contracts, OpenCV alignment, PASS/RETRY/FAIL/HUMAN_REVIEW policy, lazy ONNX boundary and synthetic benchmark
- `M8-T01..T03`: 20-case fault corpus, diagnostic guardrails and evaluation harness
- terminal failed-task recovery hardened: an explicit FAILED-task retry can reopen the job to RUNNING without permitting arbitrary mutation of failed jobs
- Python OpenTelemetry request/event correlation layer prepared and tested
- injectable ClickHouse telemetry sink boundary + ClickHouse DDL prepared and unit tested with a fake client
- PostgreSQL transactional schema/migration prepared for jobs/tasks/resources/durable command idempotency/domain events; live DB integration still pending
- deterministic simulation replay core prepared and tested; live ClickHouse retrieval integration still pending
- pre-integration Python vertical slice: three concurrent jobs through FIFO scheduling, fleet routing, vision verification and terminal completion
- pre-integration failure/retry slice for a terminal vision-task failure
- measured pre-integration performance report generator + retained benchmark artefacts
- demo capture checklist and implementation-derived CircuitHub interview stories
- four original ADRs, fault-injection matrix, benchmark catalog and portfolio evidence plan
- GitHub profile repositioned toward production robotics software
- Rust state-machine scaffold written but not locally compiled because Rust tooling is unavailable in this environment

## Verified locally
- 98 Python tests passing
- Python compileall passing
- 5-robot retained routing benchmark: zero vertex conflicts / zero edge swaps
- 20-robot retained routing benchmark: zero vertex conflicts / zero edge swaps
- CBS and cooperative A* both conflict-free on the retained intersection, corridor-with-bay and four-way-contention cases
- measured CBS evaluation supports cooperative A* as online default and CBS as reference/escalation planner on the retained cases
- synthetic vision benchmark produces labelled latency/alignment metrics
- synthetic fault corpus validates: 20 cases / 20 categories
- fixture-mode agent harness validates metric/guardrail plumbing with zero blocked oracle actions; this is explicitly not an LLM performance claim
- OpenTelemetry tests prove API span identity reaches correlated orchestrator events
- deterministic replay tests validate event ordering, machine state reconstruction and digest integrity
- Python vertical slice and retry-recovery tests pass deterministically

## Completed task count
- 26 / 43 tasks are marked `status: done` in `tasks/TASKS.json`.

## Prepared but intentionally NOT marked complete
These save future Work effort but still require real integration validation:
- `M7-T01`: PostgreSQL migration prepared; psycopg adapter + live PostgreSQL restart/idempotency tests pending
- `M7-T02`: Python OpenTelemetry plumbing tested; Rust/gRPC propagation pending
- `M7-T03`: ClickHouse schema and injectable sink tested; live ClickHouse integration/query test pending
- `M7-T04`: deterministic replay core tested; retrieval from the live telemetry store pending
- `M9`: Python pre-integration E2E skeleton exists; Rust runtime, CP-SAT, Postgres and telemetry boundaries must replace local substitutes before M9 is complete
- `M9-T03`: report generator exists and produces a pre-integration evidence report; final runtime/scheduler/database metrics are pending
- `M10`: demo/interview assets are prepared but final README/capture must use final measured integration evidence

## Reserve for Work/Codex after reset
1. `M3-T01..T05`: compile Rust runtime, typed command lifecycle, watchdog, protobuf generation, gRPC service
2. `M5-T02..T03`: install/use OR-Tools CP-SAT and benchmark against FIFO
3. finish `M7-T01..T04`: live PostgreSQL, Rust trace propagation, live ClickHouse and replay-store integration
4. real ONNX runtime/model integration beyond the tested adapter boundary if useful to final demo
5. finish `M9`: replace pre-integration local boundaries with Rust/CP-SAT/Postgres/telemetry and run golden + failure/recovery E2E
6. finish `M10`: measured-evidence README, final demo capture and interview-pack refinement
7. architectural review only after integration tests reveal a real need

## Validation labels
Completed Python pieces: locally unit/integration tested.
Rust scaffold: written, not locally compiled.
ONNX adapter: boundary tested with fake session; real ONNX runtime/model not tested here.
PostgreSQL: schema prepared; live database not validated here.
ClickHouse: adapter boundary/DDL prepared; live server not validated here.
OpenTelemetry: Python boundary tested; Rust/process propagation not yet validated.
Physical hardware: not validated.

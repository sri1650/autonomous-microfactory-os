# Task Index

Total bounded tasks: 43

## M1-T01 — Harden domain DAG/state model
**Depends on:** none
**Objective:** Add explicit task transition helpers, job terminal-state derivation, duplicate task ID safeguards and tests.
**Allowed paths:** `src/microfactory/domain/**, tests/test_domain.py`
**Verify:** `python -m pytest -q tests/test_domain.py`

## M1-T02 — Define repository interfaces
**Depends on:** M1-T01
**Objective:** Define Protocol interfaces for JobRepository, ResourceRepository and EventSink without database dependencies.
**Allowed paths:** `src/microfactory/domain/repositories.py, tests/test_repositories.py`
**Verify:** `python -m pytest -q tests/test_repositories.py`

## M1-T03 — Implement in-memory repositories
**Depends on:** M1-T02
**Objective:** Implement deterministic in-memory repositories for service tests.
**Allowed paths:** `src/microfactory/adapters/memory/**, tests/test_memory_repositories.py`
**Verify:** `python -m pytest -q tests/test_memory_repositories.py`

## M1-T04 — Implement orchestrator core
**Depends on:** M1-T03
**Objective:** Create job submission, ready-task progression, retry/cancel and idempotent state-update logic independent of web/database frameworks.
**Allowed paths:** `src/microfactory/orchestrator/**, tests/test_orchestrator.py`
**Verify:** `python -m pytest -q tests/test_orchestrator.py`

## M1-T05 — Add FastAPI boundary
**Depends on:** M1-T04
**Objective:** Expose create/get/cancel job endpoints as a thin adapter over orchestrator interfaces.
**Allowed paths:** `apps/factory_api/**, tests/test_factory_api.py`
**Verify:** `python -m pytest -q tests/test_factory_api.py`

## M2-T01 — Define deterministic simulation clock/events
**Depends on:** M1-T04
**Objective:** Implement logical tick clock and ordered immutable simulation events.
**Allowed paths:** `src/microfactory/sim/clock.py, src/microfactory/sim/events.py, tests/test_sim_clock.py`
**Verify:** `python -m pytest -q tests/test_sim_clock.py`

## M2-T02 — Implement factory world model
**Depends on:** M2-T01
**Objective:** Represent cells, stations, resources and robot poses with deterministic update semantics.
**Allowed paths:** `src/microfactory/sim/world.py, tests/test_sim_world.py`
**Verify:** `python -m pytest -q tests/test_sim_world.py`

## M2-T03 — Implement simulated machine adapter
**Depends on:** M2-T02
**Objective:** Simulate machine busy/ready/faulted execution with seeded duration/failure policy.
**Allowed paths:** `src/microfactory/sim/machines.py, tests/test_sim_machines.py`
**Verify:** `python -m pytest -q tests/test_sim_machines.py`

## M2-T04 — Implement scenario loader
**Depends on:** M2-T03
**Objective:** Load versioned JSON/YAML scenarios with explicit seed and validate schema.
**Allowed paths:** `src/microfactory/sim/scenario.py, scenarios/**, tests/test_scenarios.py`
**Verify:** `python -m pytest -q tests/test_scenarios.py`

## M2-T05 — Deterministic event digest test
**Depends on:** M2-T04
**Objective:** Prove same scenario+seed yields identical ordered event digest.
**Allowed paths:** `src/microfactory/sim/**, tests/test_sim_determinism.py`
**Verify:** `python -m pytest -q tests/test_sim_determinism.py`

## M3-T01 — Compile Rust state-machine scaffold
**Depends on:** none
**Objective:** Make the prepared Rust state machine compile cleanly and align states with protobuf contracts.
**Allowed paths:** `rust/robot_runtime/**, Cargo.toml`
**Verify:** `cargo fmt --all -- --check; cargo clippy --workspace --all-targets -- -D warnings; cargo test --workspace`

## M3-T02 — Add typed command lifecycle
**Depends on:** M3-T01
**Objective:** Add command ID, accepted/rejected, terminal result and duplicate-command idempotency semantics.
**Allowed paths:** `rust/robot_runtime/**`
**Verify:** `cargo test -p robot_runtime`

## M3-T03 — Add watchdog/heartbeat model
**Depends on:** M3-T02
**Objective:** Add monotonic heartbeat/watchdog logic as pure testable types before async networking.
**Allowed paths:** `rust/robot_runtime/**`
**Verify:** `cargo test -p robot_runtime`

## M3-T04 — Generate gRPC bindings
**Depends on:** M3-T02
**Objective:** Wire protobuf generation for Rust and Python with one schema source.
**Allowed paths:** `contracts/proto/**, rust/robot_runtime/**, python generated-contract package/**`
**Verify:** `cargo test --workspace; python -m pytest -q`

## M3-T05 — Implement Rust gRPC runtime service
**Depends on:** M3-T03, M3-T04
**Objective:** Expose SubmitCommand/GetStatus and preserve idempotency/state validation.
**Allowed paths:** `rust/robot_runtime/**, tests/integration/runtime/**`
**Verify:** `cargo test --workspace`

## M4-T01 — Harden A* baseline
**Depends on:** none
**Objective:** Add deterministic tie-breaking, path-cost helpers and benchmark fixtures.
**Allowed paths:** `src/microfactory/fleet/grid.py, tests/test_grid.py`
**Verify:** `python -m pytest -q tests/test_grid.py`

## M4-T02 — Harden reservation table
**Depends on:** M4-T01
**Objective:** Cover vertex, edge-swap, wait action and release-after-time semantics.
**Allowed paths:** `src/microfactory/fleet/reservations.py, tests/test_reservations.py`
**Verify:** `python -m pytest -q tests/test_reservations.py`

## M4-T03 — Implement time-expanded planner
**Depends on:** M4-T02
**Objective:** Plan (x,y,t) paths respecting reservations and wait actions.
**Allowed paths:** `src/microfactory/fleet/time_astar.py, tests/test_time_astar.py`
**Verify:** `python -m pytest -q tests/test_time_astar.py`

## M4-T04 — Implement cooperative multi-robot planner
**Depends on:** M4-T03
**Objective:** Plan robots in deterministic priority order and prevent vertex/edge conflicts.
**Allowed paths:** `src/microfactory/fleet/cooperative.py, tests/test_cooperative.py`
**Verify:** `python -m pytest -q tests/test_cooperative.py`

## M4-T05 — Deadlock/congestion scenarios
**Depends on:** M4-T04
**Objective:** Create corridor/intersection/contention scenarios and explicit expected behavior.
**Allowed paths:** `scenarios/fleet/**, tests/test_fleet_scenarios.py`
**Verify:** `python -m pytest -q tests/test_fleet_scenarios.py`

## M4-T06 — Fleet planner benchmark harness
**Depends on:** M4-T05
**Objective:** Emit CSV metrics for planner time, path stretch, conflicts and completion.
**Allowed paths:** `benchmarks/fleet/**`
**Verify:** `python benchmarks/fleet/run.py --robots 5 --seed 1; python benchmarks/fleet/run.py --robots 20 --seed 1`

## M4-T07 — Evaluate CBS planner
**Depends on:** M4-T06
**Objective:** Implement or justify deferring Conflict-Based Search based on benchmark value/complexity.
**Allowed paths:** `src/microfactory/fleet/cbs.py, tests/test_cbs.py, benchmarks/fleet/**`
**Verify:** `python -m pytest -q tests/test_cbs.py`

## M5-T01 — FIFO scheduler baseline
**Depends on:** M1-T04
**Objective:** Assign ready tasks by priority/creation order while respecting resource capability/availability.
**Allowed paths:** `src/microfactory/scheduler/**, tests/test_scheduler_fifo.py`
**Verify:** `python -m pytest -q tests/test_scheduler_fifo.py`

## M5-T02 — OR-Tools CP-SAT scheduler
**Depends on:** M5-T01
**Objective:** Optimise a constrained schedule with dependencies, durations and resource capacity.
**Allowed paths:** `src/microfactory/scheduler/**, tests/test_scheduler_ortools.py`
**Verify:** `python -m pytest -q tests/test_scheduler_ortools.py`

## M5-T03 — Scheduler benchmark
**Depends on:** M5-T02
**Objective:** Compare FIFO vs CP-SAT on makespan, lateness and compute time.
**Allowed paths:** `benchmarks/scheduler/**, scenarios/scheduler/**`
**Verify:** `python benchmarks/scheduler/run.py --seed 1`

## M6-T01 — Vision contract and deterministic fixtures
**Depends on:** none
**Objective:** Define observation/decision types and synthetic fixture conventions.
**Allowed paths:** `src/microfactory/vision/contracts.py, tests/fixtures/vision/**, tests/test_vision_contracts.py`
**Verify:** `python -m pytest -q tests/test_vision_contracts.py`

## M6-T02 — Fiducial/alignment baseline
**Depends on:** M6-T01
**Objective:** Implement deterministic OpenCV alignment on synthetic fixtures with error metrics.
**Allowed paths:** `src/microfactory/vision/alignment.py, tests/test_vision_alignment.py`
**Verify:** `python -m pytest -q tests/test_vision_alignment.py`

## M6-T03 — Pick/placement verification policy
**Depends on:** M6-T02
**Objective:** Implement PASS/RETRY/FAIL/HUMAN_REVIEW thresholds separated from detector implementation.
**Allowed paths:** `src/microfactory/vision/verification.py, tests/test_vision_verification.py`
**Verify:** `python -m pytest -q tests/test_vision_verification.py`

## M6-T04 — ONNX detector adapter
**Depends on:** M6-T03
**Objective:** Add injectable ONNX Runtime boundary with deterministic fake session tests.
**Allowed paths:** `src/microfactory/vision/onnx_adapter.py, tests/test_onnx_adapter.py`
**Verify:** `python -m pytest -q tests/test_onnx_adapter.py`

## M6-T05 — Vision latency/accuracy benchmark
**Depends on:** M6-T04
**Objective:** Produce machine-readable latency/decision metrics; do not claim accuracy without labelled fixtures.
**Allowed paths:** `benchmarks/vision/**`
**Verify:** `python benchmarks/vision/run.py`

## M7-T01 — PostgreSQL schema/migrations
**Depends on:** M1-T02
**Objective:** Persist jobs, tasks, resources, command identity and transactional state changes.
**Allowed paths:** `db/**, src/microfactory/adapters/postgres/**, tests/integration/postgres/**`
**Verify:** `python -m pytest -q tests/integration/postgres`

## M7-T02 — OpenTelemetry trace plumbing
**Depends on:** M1-T05, M3-T05
**Objective:** Propagate correlation/trace identity through job->task->runtime boundaries.
**Allowed paths:** `src/microfactory/telemetry/**, apps/factory_api/**, rust/robot_runtime/**, tests/integration/telemetry/**`
**Verify:** `python -m pytest -q tests/integration/telemetry`

## M7-T03 — ClickHouse telemetry sink
**Depends on:** M7-T02
**Objective:** Store/query high-volume events separately from transactional state.
**Allowed paths:** `telemetry/**, src/microfactory/telemetry/**, tests/integration/clickhouse/**`
**Verify:** `python -m pytest -q tests/integration/clickhouse`

## M7-T04 — Deterministic trace replay
**Depends on:** M2-T05, M7-T03
**Objective:** Reconstruct ordered factory/job state from recorded events and compare digest.
**Allowed paths:** `src/microfactory/replay/**, tests/test_replay.py`
**Verify:** `python -m pytest -q tests/test_replay.py`

## M8-T01 — Synthetic fault corpus
**Depends on:** M2-T05, M7-T04
**Objective:** Create versioned synthetic fault cases with expected diagnosis categories and safe allowed actions.
**Allowed paths:** `evals/faults/**`
**Verify:** `python evals/faults/validate_dataset.py`

## M8-T02 — Diagnostic-agent schema and guardrails
**Depends on:** M8-T01
**Objective:** Accept structured evidence and emit bounded hypotheses/actions that cannot bypass deterministic command validation.
**Allowed paths:** `src/microfactory/agent/**, tests/test_agent_guardrails.py`
**Verify:** `python -m pytest -q tests/test_agent_guardrails.py`

## M8-T03 — Agent evaluation harness
**Depends on:** M8-T02
**Objective:** Measure diagnosis accuracy, unsafe recommendation rate and abstention on synthetic faults.
**Allowed paths:** `evals/agent/**`
**Verify:** `python evals/agent/run.py --fixture-mode`

## M9-T01 — End-to-end golden scenario
**Depends on:** M2-T05, M3-T05, M4-T06, M5-T03, M6-T05, M7-T04
**Objective:** Run three concurrent jobs through scheduling, mover routing, simulated machine execution and vision result to terminal state.
**Allowed paths:** `tests/e2e/**, scenarios/e2e/**`
**Verify:** `python -m pytest -q tests/e2e`

## M9-T02 — Failure/recovery e2e scenario
**Depends on:** M9-T01
**Objective:** Inject blocked aisle + failed vision pick + heartbeat loss and verify bounded recovery/failure semantics.
**Allowed paths:** `tests/e2e/**, scenarios/e2e/**`
**Verify:** `python -m pytest -q tests/e2e`

## M9-T03 — Performance report generator
**Depends on:** M9-T02
**Objective:** Generate CSV/Markdown summary from measured scheduler/fleet/runtime metrics.
**Allowed paths:** `benchmarks/**, docs/generated/**`
**Verify:** `python benchmarks/report.py`

## M10-T01 — Recruiter README finalisation
**Depends on:** M9-T03
**Objective:** Replace planned claims with links to measured evidence; include concise architecture and demo instructions.
**Allowed paths:** `README.md, docs/assets/**`
**Verify:** `documentation review only`

## M10-T02 — Demo capture checklist
**Depends on:** M10-T01
**Objective:** Create exact commands/scenes/screens to record a 3-minute demo.
**Allowed paths:** `docs/demo_plan.md, docs/demo_checklist.md`
**Verify:** `documentation review only`

## M10-T03 — Interview pack
**Depends on:** M10-T01
**Objective:** Create architecture tradeoff Q&A, algorithms explanation, failure stories and honest limitations.
**Allowed paths:** `docs/interview/**`
**Verify:** `documentation review only`

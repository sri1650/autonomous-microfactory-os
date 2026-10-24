# Current State

## Completed without Codex/Work usage
- project scope, architecture and Python/Rust responsibility split locked
- Protobuf direction; PostgreSQL/ClickHouse/OpenTelemetry responsibilities decided
- low-credit agent policy and 43-task bounded task graph created
- `M1-T01` domain DAG/state hardening
- `M1-T02` repository Protocol interfaces
- `M1-T03` deterministic in-memory repositories
- `M1-T04` framework-independent orchestrator with local idempotency, retry and cancellation semantics
- `M1-T05` thin FastAPI create/get/cancel boundary
- `M2-T01` logical clock and immutable events
- `M2-T02` deterministic factory world model
- `M2-T03` seeded simulated machine adapter
- `M2-T04` versioned JSON/YAML scenario loader
- `M2-T05` same scenario + seed event-digest determinism
- `M4-T01` deterministic A* baseline + path-cost helper
- `M4-T02` temporal reservations: vertex, edge swap, wait, release-after-time
- `M4-T03` time-expanded A* with wait actions
- `M4-T04` deterministic cooperative multi-robot planner
- `M4-T05` adversarial intersection/corridor/contention scenarios
- `M4-T06` CSV fleet benchmark harness
- `M5-T01` priority/FIFO resource scheduler baseline
- `M6-T01` labelled vision contracts/fixture conventions
- `M6-T02` deterministic OpenCV alignment baseline
- `M6-T03` PASS/RETRY/FAIL/HUMAN_REVIEW policy
- `M6-T04` lazy injectable ONNX adapter boundary + fake-session tests
- `M6-T05` synthetic labelled vision benchmark harness
- `M8-T01` frozen 20-case synthetic fault corpus + validator
- `M8-T02` diagnostic schema and deterministic action guardrails
- `M8-T03` fixture-mode evaluation harness
- four ADRs, fault-injection matrix, benchmark catalog, CircuitHub interview pack and portfolio evidence plan
- GitHub profile repositioned toward production robotics software
- Rust state-machine scaffold written but not locally compiled because Rust tooling is unavailable in this environment

## Verified locally
- 80 Python tests passing
- Python compileall passing
- 5-robot and 20-robot cooperative fleet benchmark runs: zero vertex conflicts / zero edge swaps in the prepared benchmark cases
- synthetic vision benchmark produces labelled latency/alignment metrics
- synthetic fault corpus validates: 20 cases / 20 categories
- fixture-mode agent harness validates metric/guardrail plumbing with zero blocked oracle actions; this is explicitly not an LLM performance claim

## Reserve for Work/Codex after reset
1. `M3-T01..T05`: compile Rust runtime, typed command lifecycle, watchdog, protobuf generation, gRPC service
2. `M5-T02..T03`: install/use OR-Tools CP-SAT and benchmark against FIFO
3. `M7-T01..T04`: PostgreSQL, OpenTelemetry, ClickHouse, event replay integration
4. real ONNX runtime/model integration beyond the tested adapter boundary
5. `M9`: end-to-end golden and failure/recovery integration
6. `M10`: measured-evidence README, demo capture and final interview pack refinement
7. architectural review only after integration tests reveal a real need

## Validation labels
Completed Python pieces: locally unit tested.
Rust scaffold: written, not locally compiled.
ONNX adapter: boundary tested with fake session; real ONNX runtime/model not tested here.
Database/telemetry integrations: not yet implemented.
Physical hardware: not validated.

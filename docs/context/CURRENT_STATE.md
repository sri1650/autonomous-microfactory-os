# Current State

## Completed without Codex/Work usage
- project scope and architecture locked
- Python/Rust responsibility split decided
- Protobuf interface direction defined
- PostgreSQL/ClickHouse/OTel data responsibilities decided
- milestone roadmap and low-credit agent policy written
- detailed task graph created
- `M1-T01` domain DAG/state hardening complete
- `M1-T02` repository Protocol interfaces complete
- `M1-T03` deterministic in-memory repositories complete
- `M4-T01` deterministic A* baseline + path-cost helper complete
- `M4-T02` temporal reservation hardening complete (vertex, edge-swap, wait, release-after-time)
- 20-case synthetic fault corpus, failure matrix, benchmark catalog and four ADRs prepared
- CircuitHub-oriented interview pack and portfolio evidence plan prepared
- Rust state-machine scaffold written but not locally compiled (Rust toolchain unavailable in this preparation environment)

## Verified locally
- 27 focused domain/repository/fleet tests passing
- Python compileall passing
- synthetic fault corpus parses and validates structurally

## Next low-risk tasks that can be done without Codex
1. `M1-T04` orchestrator core
2. `M4-T03` time-expanded planner
3. `M4-T04` cooperative multi-robot planner
4. `M5-T01` FIFO scheduler baseline

## Tasks to reserve for Work/Codex after reset
- Rust compile/gRPC/concurrency integration
- cross-language integration
- PostgreSQL/ClickHouse/OpenTelemetry integration
- ONNX/vision runtime integration
- difficult fleet/scheduler optimisation review
- end-to-end integration and final architecture review

## Validation labels
Python completed pieces: locally unit tested.
Rust scaffold: written, not locally compiled.
Full services/simulation/database/vision: not yet implemented.
Physical hardware: not validated.

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
- `M1-T04` framework-independent orchestrator core complete, including local idempotency and retry/cancel semantics
- `M4-T01` deterministic A* baseline + path-cost helper complete
- `M4-T02` temporal reservation hardening complete
- `M4-T03` time-expanded A* with wait actions complete
- `M4-T04` deterministic cooperative multi-robot planner complete
- `M5-T01` priority/FIFO resource scheduler baseline complete
- 20-case synthetic fault corpus, failure matrix, benchmark catalog and four ADRs prepared
- CircuitHub-oriented interview pack and portfolio evidence plan prepared
- GitHub profile repositioned around production robotics/software
- Rust state-machine scaffold written but not locally compiled (Rust toolchain unavailable in this preparation environment)

## Verified locally
- 45 Python tests passing
- Python compileall passing
- synthetic fault corpus parses and validates structurally

## Next low-risk tasks that can be done without Codex
1. `M2-T01` deterministic simulation clock/events
2. `M2-T02` factory world model
3. `M2-T03` simulated machine adapter
4. `M2-T04` scenario loader
5. `M2-T05` deterministic event digest
6. `M4-T05` adversarial fleet scenarios
7. `M4-T06` fleet benchmark harness

## Tasks to reserve for Work/Codex after reset
- Rust compile/gRPC/concurrency integration
- cross-language integration
- PostgreSQL/ClickHouse/OpenTelemetry integration
- ONNX/vision runtime integration
- difficult fleet/scheduler optimisation review
- end-to-end integration and final architecture review

## Validation labels
Completed Python pieces: locally unit tested.
Rust scaffold: written, not locally compiled.
Full database/vision/cross-language services: not yet implemented.
Physical hardware: not validated.

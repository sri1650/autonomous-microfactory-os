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
- `M2-T01` logical clock and immutable event model complete
- `M2-T02` deterministic factory world model complete
- `M2-T03` seeded simulated machine adapter complete
- `M2-T04` versioned JSON/YAML scenario loader complete
- `M2-T05` same scenario + seed event-digest determinism proven
- `M1-T05` thin FastAPI create/get/cancel boundary complete
- `M4-T05` adversarial intersection/corridor/contention fleet scenarios complete
- `M4-T06` CSV fleet benchmark harness complete
- `M6-T01` labelled vision contracts/fixture conventions complete
- `M6-T02` deterministic OpenCV alignment baseline complete
- `M6-T03` PASS/RETRY/FAIL/HUMAN_REVIEW verification policy complete
- `M6-T04` injectable lazy ONNX adapter boundary + fake-session tests complete
- `M6-T05` machine-readable synthetic vision benchmark complete
- 20-case synthetic fault corpus, failure matrix, benchmark catalog and four ADRs prepared
- CircuitHub-oriented interview pack and portfolio evidence plan prepared
- GitHub profile repositioned around production robotics/software
- Rust state-machine scaffold written but not locally compiled (Rust toolchain unavailable in this preparation environment)

## Verified locally
- 76 Python tests passing
- Python compileall passing
- synthetic fault corpus parses and validates structurally

## Next low-risk tasks that can be done without Codex
1. `M8-T01` validate synthetic fault corpus
2. `M8-T02` diagnostic-agent schema + deterministic action guardrails
3. `M8-T03` fixture-mode agent evaluation harness

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

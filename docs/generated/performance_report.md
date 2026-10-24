# Pre-integration Performance Evidence

Generated from measured local benchmark artefacts. These figures are environment-specific and are not production SLAs.

## Fleet routing

| Robots | Planner ms | Total steps | Path stretch | Completion tick | Vertex conflicts | Edge swaps |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 55.445 | 130 | 1.0000 | 41 | 0 | 0 |
| 20 | 86.353 | 602 | 1.0017 | 48 | 0 | 0 |

## CBS evaluation

| Scenario | Planner | Median ms | p95 ms | Cost | Makespan | Conflict-free |
|---|---|---:|---:|---:|---:|---|
| intersection_two | cooperative | 0.049 | 0.072 | 9 | 5 | True |
| intersection_two | cbs | 0.081 | 0.215 | 9 | 5 | True |
| corridor_with_bay | cooperative | 0.054 | 0.119 | 10 | 6 | True |
| corridor_with_bay | cbs | 0.382 | 0.711 | 10 | 6 | True |
| contention_four | cooperative | 0.192 | 0.314 | 29 | 8 | True |
| contention_four | cbs | 5.302 | 7.630 | 29 | 8 | True |

## Vision alignment

- Samples: **200**
- Mean latency: **0.4531 ms**
- p95 latency: **0.4355 ms**
- Mean position-estimation error: **0.4570 px**
- Mean angle error: **0.1396 deg**
- Decisions: PASS 11, RETRY 90, FAIL 99, HUMAN_REVIEW 0

## Integration evidence

- Python vertical slice: three jobs through FIFO scheduling, conflict-free mover routing, vision verification and terminal success.
- Recovery slice: terminal vision-task failure can be explicitly retried, reopens the job, and can then succeed.
- Deterministic simulation replay core validates event ordering, machine transitions and event digest integrity.
- OpenTelemetry Python boundary propagates request span identity into correlated orchestrator events.

## Pending before final performance report

- Rust runtime/gRPC command latency and heartbeat detection
- FIFO vs OR-Tools CP-SAT makespan/lateness comparison
- live PostgreSQL restart/idempotency integration
- live ClickHouse ingestion/query measurements
- full Rust + scheduler + database + telemetry E2E scenario

The final recruiter README must only promote quantitative figures after the corresponding final integration benchmark is retained beside the claim.

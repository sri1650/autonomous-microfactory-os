# Fleet Stress Report

Deterministic cooperative-planner stress cases executed on the local pre-integration Python stack.

| Robots | Grid | Planner ms | Path stretch | Makespan | Conflict-free |
|---:|---:|---:|---:|---:|:---:|
| 10 | 20×20 | 66.460 | 1.0000 | 26 | Yes |
| 25 | 30×30 | 46.597 | 1.0417 | 41 | Yes |
| 50 | 40×40 | 243.063 | 1.0541 | 60 | Yes |

## Interpretation

- All retained 10/25/50-robot cases were conflict-free under goal-hold semantics.
- Path stretch remained close to direct Manhattan distance on these open-grid stress cases.
- These are pre-integration algorithm measurements, not production-runtime guarantees; Rust runtime, database, CP-SAT scheduling, telemetry and hardware/network effects are not included.

# Final Measured Performance Report

Measured locally on the development machine. These are software/simulation results, not production SLAs or hardware validation.

## Scheduler retained workload

| Strategy | Makespan | Mean lateness | Total tardiness | Weighted tardiness | Compute ms |
|---|---:|---:|---:|---:|---:|
| fifo | 39.0 | 6.875 | 68.0 | 274.0 | 0.0 |
| priority | 39.0 | 13.375 | 123.0 | 331.0 | 0.013 |
| spt | 39.0 | 1.125 | 32.0 | 266.0 | 0.007 |
| edd | 39.0 | 1.875 | 33.0 | 229.0 | 0.007 |
| weighted | 39.0 | 13.125 | 117.0 | 289.0 | 0.008 |
| cp_sat | 39.0 | 2.875 | 38.0 | 227.0 | 58.647 |

CP-SAT and every baseline reached a 39-tick makespan. CP-SAT produced weighted tardiness 227, versus 229 for the best heuristic (EDD).

## Fleet multi-seed scaling

| Robots | Grid | Runs | p50 ms | p95 ms | Max ms | Mean stretch | Max makespan | Conflict-free |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 10 | 20 | 10 | 6.13 | 38.53 | 64.32 | 1.0150 | 26 | True |
| 25 | 30 | 10 | 39.26 | 62.63 | 68.68 | 1.0426 | 46 | True |
| 50 | 40 | 10 | 170.52 | 389.00 | 481.28 | 1.0589 | 63 | True |
| 75 | 50 | 5 | 680.09 | 781.03 | 804.88 | 1.0631 | 85 | True |
| 100 | 60 | 5 | 1519.02 | 1737.15 | 1788.70 | 1.0635 | 113 | True |

## Rust gRPC runtime (loopback, 100 samples)

| Operation | p50 ms | p95 ms |
|---|---:|---:|
| Idempotent SubmitCommand | 0.193 | 0.414 |
| GetStatus | 0.176 | 0.331 |

## Synthetic vision alignment

- Samples: **200**
- Mean latency: **0.4531 ms**; p95: **0.4355 ms**
- Mean position error: **0.4570 px**; mean angle error: **0.1396°**

## Integration evidence

- Golden E2E: three jobs compose CP-SAT, conflict-free routing, simulated vision, PostgreSQL, three Rust gRPC processes, ClickHouse, and persisted replay.
- Failure E2E: blocked aisle replans after bounded failure, heartbeat loss rejects a mission, and a failed vision pick succeeds after one explicit retry.
- PostgreSQL restart/idempotency, cross-process W3C tracing, and live ClickHouse correlation queries have dedicated integration tests.

## Honest scope

All measurements use local software, synthetic fixtures, or simulation. No physical robot/camera validation, production deployment, safety certification, or production-scale load claim is made.

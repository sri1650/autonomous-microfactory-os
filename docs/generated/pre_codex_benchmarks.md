# Aggressive Pre-Codex Benchmark Evidence

These are local pre-integration measurements. They are not production or hardware claims.

## Scheduler heuristic baselines

| Strategy | Makespan | Mean lateness | Total tardiness | Weighted tardiness |
|---|---:|---:|---:|---:|
| priority | 39.0 | 13.38 | 123.0 | 331.0 |
| spt | 39.0 | 1.12 | 32.0 | 266.0 |
| edd | 39.0 | 1.88 | 33.0 | 229.0 |
| weighted | 39.0 | 13.12 | 117.0 | 289.0 |

These baselines are intentionally kept when CP-SAT is added so the optimiser is compared against deterministic heuristics rather than against nothing.

## Multi-seed cooperative fleet scaling

| Robots | Grid | Runs | p50 planner ms | p95 planner ms | Max ms | Mean path stretch | Max makespan | Conflict free |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 10 | 20 | 10 | 6.13 | 38.53 | 64.32 | 1.0150 | 26 | yes |
| 25 | 30 | 10 | 39.26 | 62.63 | 68.68 | 1.0426 | 46 | yes |
| 50 | 40 | 10 | 170.52 | 389.00 | 481.28 | 1.0589 | 63 | yes |
| 75 | 50 | 5 | 680.09 | 781.03 | 804.88 | 1.0631 | 85 | yes |
| 100 | 60 | 5 | 1519.02 | 1737.15 | 1788.70 | 1.0635 | 113 | yes |

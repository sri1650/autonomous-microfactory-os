# Fleet Planner Evaluation: Prioritised Cooperative A* vs CBS

Measured locally with `python benchmarks/fleet/compare_suite.py --repeats 50`. Timings are environment-specific evidence, not production SLAs.

| Scenario | Planner | Median ms | p95 ms | Sum of costs | Makespan | Conflict-free |
|---|---|---:|---:|---:|---:|---|
| intersection_two | cooperative | 0.049 | 0.072 | 9 | 5 | True |
| intersection_two | cbs | 0.081 | 0.215 | 9 | 5 | True |
| corridor_with_bay | cooperative | 0.054 | 0.119 | 10 | 6 | True |
| corridor_with_bay | cbs | 0.382 | 0.711 | 10 | 6 | True |
| contention_four | cooperative | 0.192 | 0.314 | 29 | 8 | True |
| contention_four | cbs | 5.302 | 7.630 | 29 | 8 | True |

## Decision

Keep prioritised cooperative A* as the default online planner because it produced the same path cost/makespan as CBS on the prepared adversarial cases while requiring less compute.

Keep CBS as a reference/escalation planner for tightly coupled conflicts and for validating whether prioritisation is sacrificing solution quality. Revisit the default only if broader benchmarks show a meaningful quality advantage.

The cooperative planner also now holds each robot's goal cell through the planning horizon, preventing later routes from traversing an occupied final position.

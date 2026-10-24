# ADR 0005 — Cooperative A* is the default online planner

## Status
Accepted.

## Decision
Use deterministic prioritised/cooperative time-expanded A* as the normal online fleet planner. Keep Conflict-Based Search (CBS) as a reference/escalation algorithm.

## Evidence
On retained adversarial benchmark cases, both algorithms produced equal path cost/makespan, while CBS required materially more compute. The online planner therefore favours predictable latency.

## Consequences
CBS remains useful for validation and hard contention cases, but is not the default runtime path.

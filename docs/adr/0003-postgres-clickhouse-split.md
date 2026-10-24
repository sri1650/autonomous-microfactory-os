# ADR 0003: PostgreSQL for State, ClickHouse for Telemetry

## Status
Accepted.

## Decision
Use PostgreSQL for transactional job/task/resource/command state and ClickHouse for append-heavy telemetry, traces and analytical queries.

## Why
Transactional correctness and high-volume observability have different access patterns. Mixing them would weaken either consistency semantics or analytical performance.

## Consequences
- A ClickHouse outage must not imply transactional factory-state loss.
- Terminal command/job acknowledgements depend on PostgreSQL durability, not analytics ingestion.
- Replay records carry stable correlation identifiers linking both stores.

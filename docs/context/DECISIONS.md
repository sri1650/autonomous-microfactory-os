# Architecture Decisions

## ADR-001 — Python + Rust split
Use Python for orchestration, optimisation, simulation and vision experimentation. Use Rust for the concurrent typed robot/runtime boundary. Rationale: fast iteration at high level, stronger type/concurrency guarantees near control boundaries.

## ADR-002 — Protobuf/gRPC at language boundary
A language-neutral schema prevents Python/Rust models drifting and generates typed clients/servers.

## ADR-003 — PostgreSQL + ClickHouse
PostgreSQL stores transactional factory state. ClickHouse stores high-volume telemetry/events. Do not force one database to serve both access patterns.

## ADR-004 — No message broker initially
Keep the system simpler until load/reliability tests demonstrate a broker is necessary. Internal events may be in-process; runtime RPC remains explicit.

## ADR-005 — Deterministic simulator before fancy UI
Correctness, replay and testability have priority over visualization.

## ADR-006 — FIFO baseline before OR-Tools
An optimisation algorithm must beat a measurable baseline. Implement FIFO first, then benchmark CP-SAT.

## ADR-007 — A* baseline before MAPF sophistication
Implement single-agent A*, then temporal reservations/Cooperative A*, then evaluate CBS. Do not jump directly to complex MAPF.

## ADR-008 — No autonomous agent can bypass deterministic safety gates
Agentic diagnosis may suggest actions; commands still pass typed validation, allow-lists, state checks and human approval where risk exists.

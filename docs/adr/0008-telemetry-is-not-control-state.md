# ADR 0008 — Telemetry is evidence, not authoritative control state

## Status
Accepted.

## Decision
Transactional domain/PostgreSQL state is authoritative. ClickHouse/OpenTelemetry exist for traces, analytics, debugging and replay evidence.

## Consequence
Loss or delay of telemetry must not directly mutate control decisions.

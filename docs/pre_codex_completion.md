# Aggressive Pre-Codex Completion

Implemented locally before spending Codex/Work credits:

- production-style API health/capability endpoints
- simulation-preview dashboard
- explicit retry HTTP boundary
- cooperative A* + CBS reference planner
- persistent goal-occupancy safety rule
- fleet stress harness
- replay divergence debugger and timeline frames
- FIFO + priority/SPT/EDD/weighted scheduling heuristics
- manufacturing YAML job DSL
- robot health and battery-aware mission acceptance
- deterministic chaos/fault schedule
- 100-seed domain/scheduler invariant test
- OpenTelemetry API/orchestrator Python trace correlation
- PostgreSQL schema preparation
- ClickHouse sink/DDL preparation
- deterministic Python vertical-slice and retry recovery tests

Reserved for Codex because these require the strongest cross-language/external integration value:

1. Rust runtime compile + command lifecycle + heartbeat/watchdog
2. protobuf/gRPC generation and Rust service
3. OR-Tools CP-SAT scheduler + comparison benchmark
4. live PostgreSQL adapter/container validation
5. Rust trace propagation
6. live ClickHouse integration
7. persisted deterministic replay across services
8. full-stack golden/failure E2E replacing local Python boundaries
9. final measured README/demo after those integrations pass

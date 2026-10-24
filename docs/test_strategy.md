# Verification Strategy

## Unit
- legal/illegal domain state transitions
- DAG/dependency validation
- A* path optimality on small maps
- reservation vertex conflicts
- reservation edge-swap conflicts
- scheduler baseline ordering
- Rust runtime state transition legality

## Property / fuzz candidates
- no path returned may cross blocked cells
- reservation table never accepts same vertex/time twice
- command state machine never leaves ESTOP without explicit reset policy
- replay of a deterministic scenario returns the same ordered event digest

## Integration
- submit job -> plan -> allocate resource -> dispatch simulated mover -> terminal task state
- runtime command acceptance/ack/terminal status
- database restart/recovery of unfinished job
- trace propagation across service boundaries

## Fault injection
- robot heartbeat loss
- duplicate command delivery
- delayed acknowledgement
- blocked path after route plan
- machine goes offline while job is queued
- vision confidence below threshold
- database/telemetry sink temporary outage

## Performance benchmarks
Scenarios: 5, 20 and 50 movers; 10, 100 and 500 jobs.
Metrics: jobs/hour, p50/p95 job latency, planner time, path stretch, deadlocks, conflicts resolved, robot idle time, station utilisation, telemetry ingest rate.

## Evidence gate
A README claim must point to a test, benchmark, captured simulation or hardware report.

# Three-Minute Recruiter Demo Plan

## Story

“This is a deterministic control-plane prototype for a small autonomous factory. Python handles optimisation and orchestration; Rust owns the typed robot-command boundary. I’ll show a successful three-job flow, bounded failures, replay and measured trade-offs.”

## Timeline and scenes

### 0:00–0:25 — architecture

Show the README architecture diagram. Point out PostgreSQL for durable job state, Rust/Tonic runtimes for commands, ClickHouse for correlated events, and replay as a consumer of persisted evidence.

Say: “These are local software and simulation results; no physical hardware or safety certification is claimed.”

### 0:25–1:15 — golden full-stack scenario

Show a terminal running the live E2E test. Explain that three concurrent jobs use CP-SAT, conflict-free routes, simulated vision, durable terminal state, three Rust processes, ClickHouse and digest-checked replay.

Expected result: `1 passed` for `test_full_stack_golden.py`, or `4 passed` for the complete E2E directory.

### 1:15–1:50 — bounded failures

Run the failure test with verbose output. Narrate its three injected faults:

1. a wall blocks the aisle and the first planning attempt fails deterministically;
2. opening one cell permits a bounded replan;
3. heartbeat loss makes the mover ineligible, while a failed vision pick permits exactly one explicit retry.

Expected result: `1 passed` for `test_failure_recovery.py`.

### 1:50–2:20 — operator and replay views

Show the dashboard preview, then the time-machine slider at the failed vision frame and recovered frame. Keep the “SIMULATION PREVIEW” label visible.

### 2:20–2:50 — measured trade-offs

Show `docs/generated/performance_report.md`. Highlight:

- CP-SAT weighted tardiness 227 versus EDD 229;
- conflict-free retained fleet runs through 100 robots, with p50 latency increasing from 6.13 ms to 1519.02 ms;
- Rust loopback RPC p50/p95 measurements;
- the explicit local/simulation scope statement.

### 2:50–3:00 — close

“The engineering focus is deterministic behaviour and debuggability: command idempotency, explicit failure semantics, trace continuity, retained measurements and replayable evidence.”

## Longer interview path

For a 15-minute version, open `docs/interview/CIRCUITHUB_INTERVIEW_PACK.md` and discuss the Python/Rust boundary, CP-SAT objective, cooperative-planning scalability, transaction/idempotency design, cross-process tracing and what physical validation would require.

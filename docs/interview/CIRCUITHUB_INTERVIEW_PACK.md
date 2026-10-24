# CircuitHub-Oriented Interview Pack

This is preparation material, not a script to memorise. Every claim must match what the repository has actually validated at interview time.

## 1. Why Python and Rust?
**Answer structure:** Python maximises iteration speed for orchestration, scheduling, simulation and CV/ML integration. Rust owns the runtime boundary where invalid state transitions, duplicate commands, concurrency and watchdog semantics matter. Protobuf prevents either language from becoming the contract source of truth.

## 2. How do you stop 20–50 movers colliding?
Start with a deterministic A* baseline, then add time-expanded reservations that prevent vertex conflicts and edge swaps. Cooperative A* provides a practical baseline. Benchmark it under corridor/intersection contention before deciding whether CBS complexity is justified.

## 3. How do you handle deadlocks?
Avoid pretending path planning alone solves them. Detect persistent wait cycles/resource dependencies, apply deterministic priority/backoff, release/replan reservations, and preserve bounded progress. Measure completion/deadlock count under adversarial scenarios.

## 4. Why OR-Tools?
Scheduling is a constrained optimisation problem: task dependencies, machine capabilities, capacity, priority and deadlines. FIFO provides a transparent baseline; CP-SAT is introduced only after baseline metrics exist so the value can be measured.

## 5. How do you bridge planning to a real controller?
High-level software emits typed commands with command IDs, deadlines and explicit acknowledgement semantics. The Rust runtime rejects invalid state transitions, deduplicates commands and maintains watchdog/heartbeat state. No silent retry is allowed for a command that may already have caused motion.

## 6. What happens if the network drops after a motion command?
The caller cannot assume success or blindly repeat. Reconnect/status reconciliation must determine whether the command was accepted/completed. Duplicate command IDs return the original semantic result. Safety stop behaviour belongs below the orchestration layer.

## 7. How is the system observable?
One correlation/trace context should follow API request → job → task → scheduler → fleet/runtime → vision/machine result. PostgreSQL stores business truth; ClickHouse stores high-volume events. OpenTelemetry exposes latency and causal paths.

## 8. What does deterministic replay buy you?
It turns “cannot reproduce” into a testable artefact. A scenario, seed and ordered event history reconstruct state. Replay digest mismatch exposes nondeterminism or missing side effects.

## 9. Where would an LLM/VLM be allowed?
Never directly bypassing deterministic control or safety validation. It may diagnose faults, interpret documentation or propose bounded actions. Outputs are schema-constrained, evaluated on a synthetic fault corpus and blocked from unsafe actions.

## 10. How would you prove this is production-minded rather than a demo?
Show: explicit interfaces; idempotency; failure semantics; deterministic tests; CI; benchmarks; tracing; persistent state; fault injection; replay; measured limitations. Also be explicit about what is simulation-validated versus hardware-tested.

## 11. Likely deep dives
- A* vs Cooperative A* vs CBS trade-offs
- CP-SAT scheduling complexity
- Rust ownership/concurrency choices
- exactly-once myth vs idempotent command handling
- camera confidence thresholds and human review
- database transaction boundaries
- trace propagation across Python/Rust
- replay/event ordering
- safe failure semantics

## 12. Honest limitation statement
At the current software-only stage, the project demonstrates architecture, simulation, tests and integration patterns. It does not claim production-hardware validation, safety certification, real robot stopping-distance validation or factory-scale throughput until those measurements exist.

---

# Engineering stories discovered during implementation

## 1. Goal-occupancy reservation bug
**Problem:** the prioritised fleet planner originally reserved a robot path only through its arrival timestep. A later robot could therefore legally route through the first robot's final cell even though that robot was assumed to remain there.

**Fix:** hold the goal-cell reservation through the planning horizon unless a later replanning cycle explicitly releases/moves that robot.

**Why this matters:** collision checking is not just about simultaneous path segments; terminal occupancy semantics have to be explicit.

**Interview angle:** discuss model assumptions, temporal reservations and why a benchmark that only compares overlapping path-list lengths can hide this bug.

## 2. Failed terminal task could not retry
**Problem:** if the last active task failed, `derived_terminal_state()` made the job `FAILED`. The retry API itself required the job to be `RUNNING`, making the documented retry transition impossible for that terminal task.

**Fix:** allow one tightly constrained recovery transition: a `FAILED` job may reopen to `RUNNING` only when the selected task is `FAILED` and the requested task transition is `FAILED -> READY`. Other mutations of failed jobs remain rejected.

**Interview angle:** state-machine invariants, recovery semantics, idempotency and why failure/retry behavior must be tested end-to-end rather than only at the task level.

## 3. Why CBS is not the default planner
The project implements both prioritised cooperative A* and Conflict-Based Search.

On the retained adversarial cases, both produced the same sum-of-costs and makespan, while CBS consumed more compute. Therefore the engineering decision is:
- cooperative A*: online/default planner;
- CBS: reference/escalation planner and quality comparator for tightly coupled conflicts.

This is stronger than choosing the theoretically more sophisticated algorithm by default without workload evidence.

## 4. Observability is part of correctness
The Python API boundary now starts OpenTelemetry spans, while the event-sink decorator attaches trace ID, span ID and job correlation ID to orchestrator events.

The Rust/runtime propagation is intentionally still labelled incomplete. This gives a useful discussion of where trace context must cross language/process boundaries and why ClickHouse telemetry is separated from transactional Postgres state.

## 5. Honest validation boundary
Current measurable evidence includes deterministic simulation, route conflict tests, synthetic vision fixtures, Python integration slices and trace correlation. It does **not** include production robots, certified safety functions, real factory cycle-time numbers or a live ClickHouse/Postgres deployment yet.

Use this limitation proactively in interviews; it demonstrates engineering judgement rather than weakening the project.

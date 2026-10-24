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

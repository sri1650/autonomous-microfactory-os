# Autonomous Microfactory OS — Interview Pack

Use this as preparation, not a memorised script. Every claim below is backed by the repository’s retained local evidence.

## Architecture questions

### Why Python and Rust?

Python keeps orchestration, optimisation, simulation and CV iteration fast and gives direct access to OR-Tools/OpenCV. Rust owns the concurrent robot-command/watchdog boundary where typed states and predictable failure behaviour matter. Protobuf is the language-neutral contract; neither implementation privately defines the wire format.

The trade-off is operational complexity: two build systems and cross-language tracing. The golden E2E justifies that cost by launching three real Rust/Tonic processes from the Python integration layer.

### Why PostgreSQL and ClickHouse?

PostgreSQL is business truth: current jobs/tasks and durable command IDs are transactional and survive reconnect/restart. ClickHouse is append-oriented observability: correlated event timelines are queried by job/correlation ID and replayed deterministically. Using ClickHouse as the authoritative job store would complicate transactional invariants; using PostgreSQL for high-volume trace analysis would couple operational queries to business storage.

### What is the consistency model?

The project does not claim distributed exactly-once execution. It uses at-least-once delivery assumptions plus stable command IDs and semantic idempotency. A duplicated command gets the same outcome; reuse of that ID for a different operation is rejected. PostgreSQL proves durable identity across new connections and a real container restart. Physical side effects would still require status reconciliation with the controller.

### How is the system observable?

A W3C trace context crosses Python into the Rust gRPC process. Rust creates a child span with the same trace ID and a distinct span ID. Correlation, trace and span IDs are stored with ClickHouse events, which are queried into an ordered timeline and checked with a canonical replay digest.

## Algorithm explanations

### Cooperative A* and CBS

Time-expanded A* searches `(cell, tick)` states. The reservation table forbids two robots from occupying the same vertex at the same tick and forbids opposite-direction edge swaps. Prioritised cooperative planning sorts requests deterministically and commits each route into the table; goal occupancy is held through the planning horizon.

This is fast and understandable but not complete: a poor priority order can fail despite a joint solution. Conflict-Based Search is retained as a reference/escalation planner. It branches on the earliest conflict and replans constrained agents, trading more compute for a more complete high-level search. In retained adversarial cases CBS did not improve path cost/makespan enough to justify being the default.

### CP-SAT scheduling

Each task has integer start/end variables and an interval. Dependency edges add precedence constraints; resource types use cumulative capacity constraints. The objective lexicographically favours makespan by assigning it a weight larger than the maximum possible weighted-tardiness contribution, then minimises priority-weighted tardiness. One search worker and a fixed seed keep runs deterministic.

On the retained eight-job workload, all strategies reached a 39-tick makespan. CP-SAT achieved weighted tardiness 227 versus 229 for EDD, at 58.647 ms recorded compute time. The result is a modest quality improvement with a clear compute cost—not a claim that CP-SAT always wins.

### Deterministic replay

Simulation events have logical ticks, unique monotonic sequence numbers and canonical JSON hashing. Persisted cross-service records add timestamp, event type, aggregate, correlation, trace/span identity and payload. Replay rejects mixed correlations or unordered records, reconstructs aggregate/task states and validates the digest. A first-divergence helper reports the earliest structural mismatch instead of only saying the final hash changed.

### Vision decision policy

OpenCV estimates position/angle error; deterministic thresholds map confidence and error to PASS, RETRY, FAIL or HUMAN_REVIEW. The ONNX adapter is lazy so model inference remains replaceable. Reported accuracy/latency is from synthetic fixtures only and is not a real camera or production model claim.

## Failure and recovery questions

### What happens after a network drop following a motion command?

The caller must not blindly generate a new command ID. It reconnects, queries status and retries with the original ID if appropriate. The runtime returns the original semantic response for a duplicate. Real safe-stop behaviour belongs in the controller/safety layer below this orchestration prototype.

### How are blocked aisles handled?

An unreachable aisle fails within a finite planning horizon. The E2E scenario then changes the known map by opening one cell and performs one bounded replan. The system does not loop indefinitely or silently invent a path.

### What does heartbeat loss do?

The Rust watchdog has explicit healthy/expired boundary tests. At the fleet layer, a telemetry heartbeat age of at least 2 seconds classifies the robot OFFLINE and mission acceptance returns false. Recovery requires fresh telemetry; it is not inferred from elapsed wall time alone in deterministic tests.

### How does a failed vision pick recover?

A failed final task makes the job FAILED. One tightly constrained transition permits only that failed task to move back to READY, reopens the job, increments its attempt, and allows reassignment. The E2E fixture caps recovery at one retry and verifies terminal success; other mutations of a failed job remain illegal.

## Engineering stories

### Goal-cell occupancy bug

The first cooperative planner reserved a route only through arrival. A later robot could pass through the first robot’s final cell after its path list ended. The fix holds that cell through the horizon. The lesson is that collision semantics include terminal occupancy, not only overlapping path arrays.

### Terminal retry state-machine bug

The job became FAILED as soon as its last active task failed, while retry originally required a RUNNING job. The fix added one narrow `FAILED task -> READY` recovery that also reopens the job. This was found by a vertical recovery test, not by testing task transitions alone.

### Cross-process trace extraction

The first Rust OpenTelemetry extraction path did not reliably produce a valid parent from Tonic metadata in the local test. The runtime kept the standard W3C propagator and added strict parsing of the `traceparent` fallback, then verified the exact Python trace ID and a distinct Rust child span over a real localhost RPC.

### Live-storage serialization edges

PostgreSQL required stable JSON encoding/decoding of task dependencies and payloads across fresh connections. ClickHouse `FixedString` trace/span columns can be returned as bytes, so the boundary normalises them before replay. Both issues are covered by live container tests rather than mocks alone.

## Likely deep dives

- cooperative A* completeness versus CBS cost
- CP-SAT objective weighting and capacity modelling
- idempotency versus the “exactly once” myth
- PostgreSQL transaction boundaries and restart evidence
- W3C propagation across Python/Rust
- replay ordering, canonicalization and first divergence
- confidence thresholds and human review
- watchdog semantics versus certified safety functions
- what to measure on real hardware before deployment

## Honest limitations and next validation steps

Current evidence covers local software, deterministic simulation, synthetic vision, loopback gRPC, and PostgreSQL/ClickHouse containers. It does not cover:

- real robots, motors, cameras, calibration drift or environmental variation;
- emergency stops, safety PLCs, interlocks, risk assessment or safety certification;
- stopping distance, motion envelopes, payload dynamics or network fault behaviour on hardware;
- production deployment, long-duration soak tests, security hardening or disaster recovery;
- factory-scale throughput or a production SLA.

Before hardware use, add a hardware-in-the-loop adapter, controller status reconciliation, real sensor calibration datasets, latency/jitter/dropout campaigns, safety-layer integration owned by qualified engineers, and staged validation beginning with non-actuating dry runs.

## Thirty-second close

“The project’s strongest result is not a flashy dashboard; it is the chain of evidence. The same job can be scheduled deterministically, routed without recorded conflicts, sent through a typed Rust boundary, persisted, traced across processes and replayed with a canonical digest. The limitations are explicit because the remaining gap is physical and safety validation, not another software claim.”

# Architecture

## Bounded contexts

### Factory API (Python)
Accepts jobs, queries status and exposes read-only operational views. No scheduling algorithms inside API handlers.

### Job Orchestrator (Python)
Owns job lifecycle, task DAG progression, retry/cancel policy and command idempotency.

### Scheduler (Python + OR-Tools)
Maps ready work to machines/resources under capacity, priority and dependency constraints. Starts with FIFO baseline before CP-SAT optimisation.

### Fleet Manager (Python)
Assigns movers, creates spatial/temporal routes and handles traffic conflicts. Owns planning, not motor control.

### Robot Runtime (Rust)
Owns a typed robot state machine, command acknowledgement, watchdog, heartbeat, timeouts and concurrent connection handling. It must reject invalid transitions.

### Vision Verification (Python)
Converts camera observations into alignment/pick/placement verification results with confidence and explicit uncertainty/threshold policy.

### Simulator (Python)
Deterministic world model implementing the same command/status boundaries as a physical device adapter would.

### Persistence
PostgreSQL = durable job/task/configuration/state records.
ClickHouse = high-volume telemetry and trace/event analytics.

### Observability
OpenTelemetry context flows from API request -> job -> task -> scheduler -> fleet/runtime -> vision/machine operation.

## Communication
- Protobuf contracts define commands/status/events shared by Python and Rust.
- gRPC is the planned command/status transport at the runtime boundary.
- Internal Python domain calls may remain in-process until service separation is justified.
- Avoid adding a message broker until measured need exists.

## Failure philosophy
Every external/device command has:
- command_id
- correlation_id
- deadline
- acknowledgement semantics
- idempotency policy
- explicit terminal result

No silent retries for commands that may have caused physical motion.

## Determinism
Simulation, scheduler benchmarks and fault injection accept a seed. A recorded scenario plus seed must be reproducible.

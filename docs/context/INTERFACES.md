# Interfaces

## Domain identifiers
All externally visible IDs are opaque strings/UUIDs. Never use database row numbers as protocol identity.

## Job
Fields: `job_id`, `priority`, `created_at`, `state`, ordered/graph task definitions, metadata.
States: `QUEUED -> PLANNING -> RUNNING -> SUCCEEDED | FAILED | CANCELLED`.

## Task
Fields: `task_id`, `job_id`, `kind`, `required_resource_type`, `dependencies`, `attempt`, `state`, `payload`.
States: `PENDING -> READY -> ASSIGNED -> EXECUTING -> SUCCEEDED | FAILED | CANCELLED`.

## Robot command
Fields: `command_id`, `correlation_id`, `robot_id`, `kind`, `deadline`, `payload`.
Runtime returns `ACCEPTED | REJECTED` followed by terminal `SUCCEEDED | FAILED | TIMED_OUT | CANCELLED`.

## Robot status
Fields: `robot_id`, `mode`, `pose`, `velocity`, `battery`, `active_command_id`, `faults`, `heartbeat_time`.
Modes: `OFFLINE, IDLE, HOMING, READY, EXECUTING, PAUSED, FAULTED, ESTOP`.

## Fleet route
A route is a sequence of `(x, y, t)` reservations, not only `(x, y)` geometry. Vertex and edge-swap conflicts are forbidden.

## Vision result
Fields: `observation_id`, `station_id`, `operation`, `object_id`, `pose`, `confidence`, `decision`, `reasons`, `model_version`.
Decision: `PASS | RETRY | FAIL | HUMAN_REVIEW`.

## Trace identity
Every job receives a trace/correlation ID propagated to task, robot command and vision operation spans.

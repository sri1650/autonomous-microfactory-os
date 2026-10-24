# Roadmap

## M0 — Architecture & scaffold [PREPARED]
Contracts, architecture decisions, coding-agent policy, task graph, Python planning core and CI design.

## M1 — Domain & Job Orchestration
Typed jobs/tasks/resources, state transitions, DAG validation, idempotent command semantics and orchestrator service.

## M2 — Deterministic Factory Simulator
Grid world, stations, movers, machine occupancy, task execution, seeded failure injection and reproducible event stream.

## M3 — Rust Robot Runtime
Typed state machine, command acknowledgement, watchdog/heartbeat, timeout semantics, concurrent connection handling and gRPC server.

## M4 — Fleet & Traffic Management
A*, temporal reservations, Cooperative A*, deadlock detection, later Conflict-Based Search; benchmarks with 5/20/50 movers.

## M5 — Scheduler
FIFO baseline followed by OR-Tools CP-SAT scheduling across resources, priorities, machine availability and transport dependencies.

## M6 — Vision Verification
Synthetic camera fixtures, fiducial/centroid alignment, pick/placement verification, PyTorch-to-ONNX model boundary and latency/accuracy benchmark.

## M7 — Persistence, Telemetry & Replay
PostgreSQL event/state persistence, OpenTelemetry traces, ClickHouse telemetry, job timeline view and deterministic failure replay.

## M8 — Agentic Fault Diagnosis
LLM/VLM-style diagnostic interface behind strict schema/safety gates, synthetic fault corpus and evaluation harness. No autonomous unsafe actuation.

## M9 — Integration & Performance
End-to-end scenario tests, throughput/deadlock/recovery metrics, profiling and architecture review.

## M10 — Portfolio Evidence
Demo script, architecture diagrams, benchmark tables, screenshots/video checklist, interview questions and CV bullets based only on completed evidence.

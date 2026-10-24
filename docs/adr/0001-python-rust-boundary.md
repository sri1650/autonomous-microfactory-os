# ADR 0001: Python / Rust Boundary

## Status
Accepted for initial architecture.

## Decision
Use Python for orchestration, scheduling, simulation, vision integration and experiment velocity. Use Rust for the robot/runtime boundary where typed state transitions, concurrency, command idempotency, watchdogs and lower-level device integration benefit from stricter guarantees.

## Why
The portfolio needs to demonstrate architectural judgement, not language maximalism. A pure-Rust rewrite would slow iteration in optimisation/vision; a pure-Python runtime would not showcase the systems boundary CircuitHub explicitly values.

## Consequences
- Protobuf is the language-neutral contract source.
- High-level algorithms remain replaceable without changing runtime semantics.
- Cross-language integration is tested explicitly.

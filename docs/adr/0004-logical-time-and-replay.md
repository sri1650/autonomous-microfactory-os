# ADR 0004: Logical Time for Deterministic Simulation

## Status
Accepted.

## Decision
Simulation and benchmark code uses a logical monotonic tick plus explicit seed instead of wall-clock timing for state progression.

## Why
Failures must be reproducible. Wall-clock scheduling creates nondeterministic ordering that makes debugging and benchmark comparison unreliable.

## Consequences
- Event order is stable for the same scenario + seed.
- Real adapters translate monotonic/wall time at the system boundary.
- Replay compares event/state digests to detect divergence.

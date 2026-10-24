# Performance Targets (Portfolio, not production SLA)

These are engineering targets to guide benchmarks, not claims until measured.

- deterministic simulation reproducibility: identical event digest for same scenario+seed
- zero vertex or edge-swap collisions in accepted fleet plans
- 20-mover routing benchmark: p95 planning cycle < 250 ms on developer machine target
- 50-mover routing benchmark: p95 planning cycle < 1 s target
- scheduler: demonstrate measurable improvement over FIFO on at least one constrained scenario
- robot runtime heartbeat fault detection: configurable, test default 1 s
- duplicate command: never causes duplicate terminal actuation in simulation
- trace correlation: 100% of task/command/vision events contain job correlation identity

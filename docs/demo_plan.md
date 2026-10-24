# Demo Plan

## Recruiter demo — 3 minutes
1. Submit three PCB-style jobs with different priorities.
2. Show scheduler selecting machines and movers.
3. Visualize multiple movers reserving routes through a constrained corridor.
4. Inject a blocked aisle; show replanning without collision.
5. Inject a failed pick verification; show retry policy.
6. Open the trace for one job and follow it from API to terminal result.
7. Replay the failed job deterministically.

## Interview deep dive — 15 minutes
- architecture and ownership
- Python vs Rust tradeoff
- command idempotency and motion semantics
- temporal path conflicts/deadlock strategy
- scheduling baseline vs optimiser metrics
- tracing/replay design
- simulation vs hardware-validation boundary

## Required evidence assets before calling project complete
- architecture SVG
- 1 end-to-end demo video
- benchmark CSV + chart
- trace screenshot
- replay screenshot/video
- CI passing screenshot/badge
- performance/limitations section in README

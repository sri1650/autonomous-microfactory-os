# Work/Codex Resume Prompt — Credit-Efficient

Continue the existing `autonomous-microfactory-os` repository. Do **not** redesign or regenerate completed Python work.

Read only these first:
1. `AGENTS.md`
2. `docs/context/CURRENT_STATE.md`
3. `docs/context/ARCHITECTURE.md`
4. `tasks/TASKS.json`
5. the files needed for the next task

## Current verified state
- 98 Python tests pass locally.
- Completed task IDs are marked `status: done` in `tasks/TASKS.json`.
- Existing Git history is intentional; preserve it.
- Python architecture, simulation, fleet/CBS planning, vision verification, replay core, Python trace correlation, pre-integration E2E skeleton and agent-eval scaffolding are already implemented.

## First action after reset
Run the existing Python test suite. If green, do not modify it.

Then attempt `M3-T01`: compile the prepared Rust state-machine scaffold.

Use Standard speed / minimum reasoning sufficient for the task. Escalate only if deterministic tool output shows a blocker.

## Priority after Rust
1. M3-T01..T05 Rust/gRPC
2. M5-T02 OR-Tools CP-SAT + M5-T03 benchmark
3. M7 live persistence/observability integration (schema/adapters/replay core are already prepared)
4. M9 replace the prepared Python vertical slice with Rust/CP-SAT/Postgres/telemetry boundaries
5. M10 measured-evidence documentation

## Hard rules
- one bounded task at a time
- use `allowed_paths` from `tasks/TASKS.json`
- run the task's exact `verify` commands
- max two repair attempts before blocker escalation
- no architecture rewrite unless a failing integration test proves a contradiction
- do not claim hardware validation
- do not replace deterministic tests with LLM judgement

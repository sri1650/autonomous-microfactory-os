# AGENTS.md — Low-credit engineering policy

## Goal
Build `autonomous-microfactory-os` as a technically defensible robotics software portfolio project while minimizing expensive-model usage.

## Mandatory context order
Before editing code, read only:
1. `docs/context/PROJECT.md`
2. `docs/context/ARCHITECTURE.md`
3. `docs/context/INTERFACES.md`
4. `docs/context/CURRENT_STATE.md`
5. the assigned task entry in `tasks/TASKS.json`
6. only the files listed in that task's `allowed_paths`

Do not scan the whole repository unless the task explicitly requires it.

## Work loop
PLAN -> IMPLEMENT -> RUN DETERMINISTIC CHECKS -> FIX (max 2 attempts) -> UPDATE CURRENT_STATE -> COMMIT

## Token/credit rules
- Use deterministic tools before reasoning: pytest, ruff, mypy, cargo fmt, cargo clippy, cargo test, integration scripts.
- Do not rewrite working code for style alone.
- Do not regenerate unchanged documentation.
- One task = one primary responsibility.
- Keep explanations short; prefer patch + commands + results.
- Maximum two repair attempts per failing task. If still blocked, write `docs/context/BLOCKED.md` and escalate.
- High-capability reasoning is reserved for architecture, cross-component bugs, milestone reviews and final review.

## Project integrity
Never claim physical-hardware validation unless it has actually occurred. Label evidence as one of:
- unit tested
- integration tested
- simulation validated
- hardware validated

## Architecture constraints
- High-level orchestration, optimisation and experimentation: Python.
- Typed concurrent robot/runtime boundary: Rust.
- Language-neutral commands/status: Protobuf/gRPC.
- Durable factory/job state: PostgreSQL.
- High-volume telemetry/traces: OpenTelemetry -> ClickHouse.
- Planning algorithms must be deterministic under a supplied random seed.
- Domain logic must not depend directly on web frameworks or database clients.

## Completion rule
A task is complete only when its specified `verify` commands pass or the task explicitly documents why a command requires an unavailable external environment.

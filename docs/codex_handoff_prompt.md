# Work Handoff — Autonomous Microfactory OS

Continue the attached `autonomous-microfactory-os` repository.

This project has been aggressively pre-built outside Work to conserve Codex/GPT usage. Treat the repository, `tasks/TASKS.json`, `docs/context/CURRENT_STATE.md`, and the handoff manifest as the source of truth.

## Mandatory first steps

1. Extract/open the repository.
2. Read:
   - `AGENTS.md`
   - `tasks/TASKS.json`
   - `docs/context/CURRENT_STATE.md`
   - `docs/context/ARCHITECTURE.md`
   - `docs/context/INTERFACES.md`
   - `docs/context/DECISIONS.md`
3. Run:
   ```bash
   python tools/pre_codex_gate.py
   ```
4. If the gate passes, do **not** redesign or rewrite passing pre-Codex work.
5. Start the first dependency-ready incomplete formal task.

## Current baseline

- 140 Python tests passing at handoff.
- 26/43 formal tasks complete.
- Multi-seed cooperative fleet benchmarks retained through 100 robots with zero conflicts in the retained runs.
- Dashboard, replay time-machine preview, YAML job DSL, heuristic scheduler baselines, health/battery model, fault schedules, replay/debugging, benchmark artefacts and Python integration slices are already prepared.
- CP-SAT problem extraction is prepared; actual OR-Tools solving is not.
- PostgreSQL codec/repository SQL boundary is prepared; live psycopg/Postgres validation is not.
- Python W3C trace carrier helpers are prepared; Rust/gRPC propagation is not.
- ClickHouse schema/sink boundary is prepared; live ClickHouse validation is not.

## Do not redo

Do not spend tokens recreating:
- domain/state models
- FastAPI job API
- retry semantics
- YAML job DSL
- dashboard/time-machine preview
- A*/time-A*/reservations/cooperative planner/CBS
- goal-occupancy safety hardening
- scheduler heuristic baselines
- fleet stress/property tests
- robot health/battery model
- deterministic fault schedules
- OpenCV vision verification
- deterministic simulator/replay/divergence tools
- Python trace correlation/carrier helpers
- PostgreSQL serialization/SQL adapter boundary
- ClickHouse injectable sink boundary
- Python pre-integration E2E
- benchmark/report plumbing
- ADRs/interview evidence already present

Only change completed code if a compiler/test/integration failure proves it necessary.

## Codex-only remaining mission

### A. Rust / gRPC
Complete M3-T01 through M3-T05:
- compile existing Rust scaffold
- typed command lifecycle
- duplicate command idempotency
- heartbeat/watchdog/timeout model
- protobuf generation from the existing schema
- Rust + Python bindings from one schema source
- gRPC SubmitCommand/GetStatus service
- tests and Python orchestration integration

Verify with Cargo, not LLM judgement.

### B. OR-Tools
Complete M5-T02/M5-T03:
- use the existing `scheduler/cp_sat.py` problem extraction
- implement real CP-SAT resource/dependency scheduling
- add deterministic tests
- compare CP-SAT against existing FIFO/priority/SPT/EDD/weighted baselines
- report makespan, lateness and compute time

### C. Live persistence
Complete M7-T01:
- use existing migration and Postgres adapter/codec boundary
- wire real psycopg
- run Postgres container integration tests
- prove restart persistence and command idempotency
- preserve domain isolation

### D. Cross-process observability
Complete M7-T02/M7-T03:
- propagate W3C trace context Python -> gRPC -> Rust
- link job/task/runtime spans
- validate correlation IDs
- connect existing ClickHouse sink to a real server/client
- query retained telemetry in integration tests

### E. Persisted deterministic replay
Complete M7-T04:
- source recorded events from the real persistence/telemetry path
- replay a failed run
- reproduce the causal sequence/digest
- expose first divergence using existing replay debugger

### F. Final E2E
Complete M9:
- reuse the existing three-job and failure/retry scenario intent
- replace local Python boundaries with Rust + CP-SAT + Postgres + telemetry
- add blocked aisle, failed vision and heartbeat-loss scenario
- produce measured final performance report

### G. Final portfolio finish
Only after all integration tests pass:
- final README
- architecture diagram
- demo commands/screens
- measured benchmark links
- interview pack
- explicit simulation-vs-hardware limitations

Never claim physical hardware or production deployment.

## Low-credit execution policy

- One bounded task at a time.
- Minimal relevant context only.
- Deterministic tools before model reasoning.
- Max two repair attempts; then write a blocker and escalate only that blocker.
- Strongest reasoning model only for hard architecture/numerical/concurrency/cross-service failures.
- Commit after verified milestones.
- Do not perform broad stylistic refactors.

## Definition of done

All formal task acceptance checks pass; Rust and Python tests pass; CP-SAT is measured against baselines; Postgres/ClickHouse are live-tested; W3C trace context crosses Python/Rust; persisted replay reproduces a failure; final E2E scenarios pass; final README uses measured evidence and accurately states that hardware validation is absent.

At completion report:
- repo URL
- final commit SHA
- test summary
- benchmark summary
- demo commands
- simulation-only/hardware-unvalidated boundaries

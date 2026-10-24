# Microfactory OS Demo Capture Checklist

This checklist separates what can be recorded **now** from what must wait for the Rust/CP-SAT/database/telemetry integration.

## Pre-integration evidence — recordable now

### 1. Entire Python verification suite
```bash
python -m pytest -q
python -m compileall -q src tests
```
Capture: final passing test count.

### 2. Three-job vertical slice
```bash
python -m pytest -q tests/e2e/test_python_vertical_slice.py -vv
```
Explain: three jobs are priority-scheduled, movers receive conflict-free routes, vision verification passes, and every job reaches `SUCCEEDED`.

### 3. Failure/retry recovery
```bash
python -m pytest -q tests/e2e/test_retry_recovery_prework.py -vv
```
Explain: a failed final vision task puts the job into `FAILED`; an explicit retry safely reopens only that failed task/job, increments the attempt count, and allows eventual success.

### 4. Fleet planner trade-off
```bash
python benchmarks/fleet/compare_suite.py --repeats 50
```
Show: cooperative A* and CBS produce conflict-free solutions on the adversarial scenarios; CBS is retained as a reference/escalation planner rather than the online default.

### 5. 20-robot benchmark
```bash
python benchmarks/fleet/run.py --robots 20 --seed 1002 --size 40
```
Show: zero vertex conflicts / zero edge swaps in the retained benchmark case.

### 6. Vision benchmark
```bash
python benchmarks/vision/run.py --samples 200 --seed 3001
```
Explain: deterministic fixture-based alignment and PASS/RETRY/FAIL policy; this is not a real camera/model accuracy claim.

### 7. Replay integrity
```bash
python -m pytest -q tests/test_replay.py -vv
```
Explain: recorded simulation events are order-validated, replayed through machine state transitions, and checked against the original event digest.

### 8. OpenTelemetry correlation
```bash
python -m pytest -q tests/integration/telemetry/test_tracing.py -vv
```
Explain: API request span identity reaches correlated domain events. Rust propagation remains pending.

### 9. Regenerate the evidence report
```bash
python benchmarks/report.py
cat docs/generated/performance_report.md
```

## Final 3-minute recruiter demo — capture after Work integration

1. `docker compose up` full stack: API, Postgres, ClickHouse, robot runtime and simulator.
2. Submit three PCB-style jobs with distinct priorities.
3. Show CP-SAT allocation and mover paths.
4. Inject blocked aisle and show bounded replan.
5. Inject failed visual pick and show retry/recovery.
6. Drop robot heartbeat and show runtime safe degradation/unavailability.
7. Open one OpenTelemetry trace from API through runtime/vision/recovery.
8. Query the corresponding ClickHouse events by correlation ID.
9. Replay the failed run and verify the deterministic digest.
10. Finish on the benchmark/limitations section of the README.

## Recording rule
Never imply physical factory or safety-certified validation. Say "simulated", "unit/integration tested", or "measured on the retained benchmark" exactly as supported by evidence.

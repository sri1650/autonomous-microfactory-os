#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.domain.models import JobRecord, ResourceRecord, TaskDefinition, TaskRecord
from microfactory.orchestrator import Orchestrator
from microfactory.scheduler.cp_sat import build_problem, solve_cp_sat
from microfactory.scheduler.heuristics import Heuristic, rank_ready_tasks


@dataclass(frozen=True)
class Result:
    strategy: str
    makespan: float
    mean_lateness: float
    total_tardiness: float
    weighted_tardiness: float
    compute_ms: float


def load_workload(path: Path) -> list[JobRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    jobs = []
    for item in raw["jobs"]:
        service = Orchestrator(InMemoryJobRepository(), InMemoryEventSink())
        job = JobRecord(
            item["id"],
            int(item["priority"]),
            {
                "work": TaskRecord(
                    TaskDefinition(
                        "work",
                        "PROCESS",
                        "machine",
                        payload={
                            "duration": int(item["duration"]),
                            "due_tick": int(item["due_tick"]),
                        },
                    )
                )
            },
        )
        jobs.append(service.submit_job(job, command_id=f"submit:{item['id']}").job)
    return jobs


def evaluate_order(jobs: list[JobRecord], strategy: str, order, compute_ms: float) -> Result:
    now = 0.0
    lateness = []
    tardiness = []
    weighted = []
    for item in order:
        job = item.job if hasattr(item, "job") else item
        task = item.task if hasattr(item, "task") else job.tasks["work"]
        duration = float(task.definition.payload["duration"])
        due = float(task.definition.payload["due_tick"])
        now += duration
        late = now - due
        tardy = max(0.0, late)
        lateness.append(late)
        tardiness.append(tardy)
        weighted.append(tardy * max(1, job.priority))
    return Result(
        strategy,
        now,
        sum(lateness) / len(lateness),
        sum(tardiness),
        sum(weighted),
        compute_ms,
    )


def benchmark(jobs: list[JobRecord]) -> list[Result]:
    rows = []
    started = perf_counter()
    fifo_order = list(jobs)
    rows.append(evaluate_order(jobs, "fifo", fifo_order, (perf_counter() - started) * 1_000))

    for strategy in Heuristic:
        started = perf_counter()
        order = rank_ready_tasks(jobs, strategy)
        elapsed = (perf_counter() - started) * 1_000
        rows.append(evaluate_order(jobs, strategy.value, order, elapsed))

    problem = build_problem(jobs, [ResourceRecord("machine-1", "machine")])
    solution = solve_cp_sat(problem)
    tasks = {(task.job_id, task.task_id): task for task in solution.tasks}
    lateness = []
    tardiness = []
    weighted = []
    for job in jobs:
        task = job.tasks["work"]
        scheduled = tasks[(job.job_id, "work")]
        due = int(task.definition.payload["due_tick"])
        late = scheduled.end - due
        tardy = max(0, late)
        lateness.append(late)
        tardiness.append(tardy)
        weighted.append(tardy * max(1, job.priority))
    rows.append(
        Result(
            "cp_sat",
            float(solution.makespan),
            sum(lateness) / len(lateness),
            float(sum(tardiness)),
            float(sum(weighted)),
            solution.solver_ms,
        )
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "scenarios" / "scheduler" / "baseline_workload.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = benchmark(load_workload(args.scenario))
    target = args.output.open("w", newline="", encoding="utf-8") if args.output else sys.stdout
    try:
        writer = csv.writer(target)
        writer.writerow(
            [
                "seed",
                "strategy",
                "makespan",
                "mean_lateness",
                "total_tardiness",
                "weighted_tardiness",
                "compute_ms",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    args.seed,
                    row.strategy,
                    row.makespan,
                    round(row.mean_lateness, 3),
                    row.total_tardiness,
                    row.weighted_tardiness,
                    round(row.compute_ms, 3),
                ]
            )
    finally:
        if args.output:
            target.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

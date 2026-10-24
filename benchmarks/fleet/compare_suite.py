#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.fleet.cbs import first_conflict, plan_cbs  # noqa: E402
from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively  # noqa: E402
from microfactory.fleet.grid import Grid  # noqa: E402


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("values cannot be empty")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def load_case(path: Path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    grid = Grid(
        int(raw["grid"]["width"]),
        int(raw["grid"]["height"]),
        frozenset(tuple(cell) for cell in raw["grid"].get("blocked", [])),
    )
    requests = [
        RobotPlanRequest(
            str(robot["id"]),
            tuple(robot["start"]),
            tuple(robot["goal"]),
            priority=int(robot.get("priority", 0)),
        )
        for robot in raw["robots"]
    ]
    return raw, grid, requests


def run_many(name, planner, repeats: int):
    timings = []
    last_plans = None
    for _ in range(repeats):
        started = perf_counter()
        last_plans = planner()
        timings.append((perf_counter() - started) * 1000.0)
    assert last_plans is not None
    return {
        "planner": name,
        "median_ms": statistics.median(timings),
        "p95_ms": percentile(timings, 0.95),
        "sum_of_costs": sum(len(path) - 1 for path in last_plans.values()),
        "makespan": max((len(path) - 1 for path in last_plans.values()), default=0),
        "conflict_free": first_conflict(last_plans) is None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeats <= 0:
        raise SystemExit("--repeats must be positive")

    scenario_paths = [
        ROOT / "scenarios/fleet/intersection_two.json",
        ROOT / "scenarios/fleet/corridor_with_bay.json",
        ROOT / "scenarios/fleet/contention_four.json",
    ]
    rows = []
    for path in scenario_paths:
        raw, grid, requests = load_case(path)
        max_time = int(raw["max_time"])
        coop = run_many(
            "cooperative",
            lambda: plan_cooperatively(grid, requests, max_time=max_time)[0],
            args.repeats,
        )
        cbs = run_many(
            "cbs",
            lambda: plan_cbs(grid, requests, max_time=max_time),
            args.repeats,
        )
        for result in (coop, cbs):
            rows.append({"scenario": raw["id"], **result})

    fieldnames = list(rows[0])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return 0 if all(row["conflict_free"] for row in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())

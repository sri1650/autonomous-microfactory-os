#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.fleet.cbs import first_conflict, plan_cbs  # noqa: E402
from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively  # noqa: E402
from microfactory.fleet.grid import Grid  # noqa: E402


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


def metrics(name: str, plans: dict[str, list[tuple[int, int]]], elapsed_ms: float):
    conflict = first_conflict(plans)
    return {
        "planner": name,
        "planner_ms": elapsed_ms,
        "sum_of_costs": sum(len(path) - 1 for path in plans.values()),
        "makespan": max((len(path) - 1 for path in plans.values()), default=0),
        "conflict_free": conflict is None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        type=Path,
        default=ROOT / "scenarios/fleet/contention_four.json",
    )
    parser.add_argument("--csv", action="store_true")
    args = parser.parse_args()

    raw, grid, requests = load_case(args.scenario)
    max_time = int(raw.get("max_time", max(20, grid.width * grid.height * 4)))

    start = perf_counter()
    cooperative, _ = plan_cooperatively(grid, requests, max_time=max_time)
    coop_ms = (perf_counter() - start) * 1000.0

    start = perf_counter()
    cbs = plan_cbs(grid, requests, max_time=max_time)
    cbs_ms = (perf_counter() - start) * 1000.0

    rows = [metrics("cooperative", cooperative, coop_ms), metrics("cbs", cbs, cbs_ms)]
    if args.csv:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    else:
        print(json.dumps({"scenario": raw["id"], "results": rows}, indent=2))

    return 0 if all(row["conflict_free"] for row in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())

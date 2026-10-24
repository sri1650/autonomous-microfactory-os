#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively  # noqa: E402
from microfactory.fleet.grid import Grid, manhattan  # noqa: E402


def generate_requests(robot_count: int, seed: int, size: int) -> list[RobotPlanRequest]:
    if robot_count * 2 > size * size:
        raise ValueError("grid is too small for unique starts/goals")
    rng = random.Random(seed)
    cells = [(x, y) for y in range(size) for x in range(size)]
    rng.shuffle(cells)
    starts = cells[:robot_count]
    goals = cells[robot_count : robot_count * 2]
    return [
        RobotPlanRequest(f"r{i:03d}", starts[i], goals[i], priority=robot_count - i)
        for i in range(robot_count)
    ]


def validate(plans: dict[str, list[tuple[int, int]]]) -> tuple[int, int]:
    vertex_conflicts = 0
    edge_swaps = 0
    ids = sorted(plans)
    for i, left in enumerate(ids):
        lp = plans[left]
        for right in ids[i + 1 :]:
            rp = plans[right]
            horizon = min(len(lp), len(rp))
            for t in range(horizon):
                if lp[t] == rp[t]:
                    vertex_conflicts += 1
            for t in range(horizon - 1):
                if lp[t] == rp[t + 1] and lp[t + 1] == rp[t]:
                    edge_swaps += 1
    return vertex_conflicts, edge_swaps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--robots", type=int, default=5)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--size", type=int, default=30)
    args = parser.parse_args()

    if args.robots <= 0:
        raise SystemExit("--robots must be positive")

    grid = Grid(args.size, args.size)
    requests = generate_requests(args.robots, args.seed, args.size)
    direct = sum(manhattan(request.start, request.goal) for request in requests)

    started = perf_counter()
    plans, _ = plan_cooperatively(
        grid,
        requests,
        max_time=args.size * args.size * 2,
    )
    elapsed_ms = (perf_counter() - started) * 1000.0

    steps = sum(len(path) - 1 for path in plans.values())
    completion_tick = max(len(path) - 1 for path in plans.values())
    vertex_conflicts, edge_swaps = validate(plans)
    stretch = steps / direct if direct else 1.0

    writer = csv.writer(sys.stdout)
    writer.writerow(
        [
            "robots",
            "seed",
            "grid_size",
            "planner_ms",
            "total_steps",
            "direct_steps",
            "path_stretch",
            "completion_tick",
            "vertex_conflicts",
            "edge_swaps",
        ]
    )
    writer.writerow(
        [
            args.robots,
            args.seed,
            args.size,
            f"{elapsed_ms:.3f}",
            steps,
            direct,
            f"{stretch:.4f}",
            completion_tick,
            vertex_conflicts,
            edge_swaps,
        ]
    )
    return 0 if vertex_conflicts == 0 and edge_swaps == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

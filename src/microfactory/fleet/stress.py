from __future__ import annotations

from dataclasses import dataclass
import random
from time import perf_counter

from .cbs import first_conflict
from .cooperative import RobotPlanRequest, plan_cooperatively
from .grid import Grid, manhattan


@dataclass(frozen=True, slots=True)
class StressResult:
    robots: int
    seed: int
    grid_size: int
    planner_ms: float
    total_steps: int
    direct_steps: int
    path_stretch: float
    makespan: int
    conflict_free: bool


def generate_unique_requests(
    robot_count: int,
    *,
    grid_size: int,
    seed: int,
) -> list[RobotPlanRequest]:
    if robot_count <= 0:
        raise ValueError("robot_count must be positive")
    if grid_size <= 1:
        raise ValueError("grid_size must be > 1")
    if robot_count * 2 > grid_size * grid_size:
        raise ValueError("grid too small for unique starts/goals")

    rng = random.Random(seed)
    cells = [(x, y) for y in range(grid_size) for x in range(grid_size)]
    rng.shuffle(cells)
    starts = cells[:robot_count]
    goals = cells[robot_count:robot_count * 2]
    return [
        RobotPlanRequest(
            f"r{i:03d}",
            starts[i],
            goals[i],
            priority=robot_count - i,
        )
        for i in range(robot_count)
    ]


def run_stress_case(robot_count: int, *, grid_size: int, seed: int) -> StressResult:
    grid = Grid(grid_size, grid_size)
    requests = generate_unique_requests(robot_count, grid_size=grid_size, seed=seed)
    direct = sum(manhattan(r.start, r.goal) for r in requests)
    started = perf_counter()
    plans, _ = plan_cooperatively(
        grid,
        requests,
        max_time=grid_size * grid_size * 2,
    )
    elapsed_ms = (perf_counter() - started) * 1000.0
    total_steps = sum(len(path) - 1 for path in plans.values())
    makespan = max(len(path) - 1 for path in plans.values()) if plans else 0
    return StressResult(
        robots=robot_count,
        seed=seed,
        grid_size=grid_size,
        planner_ms=elapsed_ms,
        total_steps=total_steps,
        direct_steps=direct,
        path_stretch=(total_steps / direct) if direct else 1.0,
        makespan=makespan,
        conflict_free=first_conflict(plans) is None,
    )


def run_stress_suite(cases: list[tuple[int, int, int]]) -> list[StressResult]:
    """Run deterministic (robots, grid_size, seed) cases in supplied order."""
    return [
        run_stress_case(robots, grid_size=size, seed=seed)
        for robots, size, seed in cases
    ]

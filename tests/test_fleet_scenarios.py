import json
from pathlib import Path

import pytest

from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively
from microfactory.fleet.grid import Grid

ROOT = Path(__file__).parents[1]


def load_case(name):
    return json.loads((ROOT / "scenarios/fleet" / name).read_text())


def timed(path, start_time=0):
    return [(cell, start_time + i) for i, cell in enumerate(path)]


def assert_no_conflicts(plans):
    ids = sorted(plans)
    timed_paths = {rid: timed(path) for rid, path in plans.items()}
    for i, left in enumerate(ids):
        lmap = {t: cell for cell, t in timed_paths[left]}
        lpath = plans[left]
        ledges = {(lpath[j], lpath[j + 1], j) for j in range(len(lpath) - 1)}
        for right in ids[i + 1 :]:
            rmap = {t: cell for cell, t in timed_paths[right]}
            common_times = set(lmap) & set(rmap)
            assert all(lmap[t] != rmap[t] for t in common_times)
            rpath = plans[right]
            redges = {(rpath[j], rpath[j + 1], j) for j in range(len(rpath) - 1)}
            assert not any((b, a, t) in redges for a, b, t in ledges)


@pytest.mark.parametrize(
    "filename",
    ["intersection_two.json", "corridor_with_bay.json", "contention_four.json"],
)
def test_adversarial_fleet_scenarios(filename):
    raw = load_case(filename)
    grid = Grid(
        raw["grid"]["width"],
        raw["grid"]["height"],
        frozenset(tuple(cell) for cell in raw["grid"].get("blocked", [])),
    )
    requests = [
        RobotPlanRequest(
            robot["id"],
            tuple(robot["start"]),
            tuple(robot["goal"]),
            priority=robot.get("priority", 0),
        )
        for robot in raw["robots"]
    ]
    plans, _ = plan_cooperatively(grid, requests, max_time=raw["max_time"])
    assert set(plans) == {request.robot_id for request in requests}
    assert_no_conflicts(plans)

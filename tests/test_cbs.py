import pytest

from microfactory.fleet.cbs import first_conflict, plan_cbs
from microfactory.fleet.cooperative import RobotPlanRequest
from microfactory.fleet.grid import Grid


def test_detects_vertex_conflict():
    conflict = first_conflict(
        {
            "a": [(0, 0), (1, 0), (2, 0)],
            "b": [(2, 0), (1, 0), (0, 0)],
        }
    )
    assert conflict is not None
    assert conflict.kind == "vertex"
    assert conflict.cell == (1, 0)
    assert conflict.time == 1


def test_detects_edge_swap_conflict():
    conflict = first_conflict(
        {
            "a": [(0, 0), (1, 0)],
            "b": [(1, 0), (0, 0)],
        }
    )
    assert conflict is not None
    assert conflict.kind == "edge"
    assert conflict.time == 0


def test_cbs_solves_intersection_without_conflict():
    grid = Grid(5, 5)
    plans = plan_cbs(
        grid,
        [
            RobotPlanRequest("east-west", (0, 2), (4, 2)),
            RobotPlanRequest("north-south", (2, 0), (2, 4)),
        ],
        max_time=20,
    )
    assert plans["east-west"][-1] == (4, 2)
    assert plans["north-south"][-1] == (2, 4)
    assert first_conflict(plans) is None


def test_cbs_solves_bidirectional_corridor_with_bay():
    grid = Grid(
        5,
        3,
        frozenset({(0, 0), (1, 0), (4, 0), (0, 2), (1, 2), (3, 2), (4, 2)}),
    )
    plans = plan_cbs(
        grid,
        [
            RobotPlanRequest("r1", (0, 1), (4, 1)),
            RobotPlanRequest("r2", (4, 1), (0, 1)),
        ],
        max_time=30,
    )
    assert first_conflict(plans) is None
    assert plans["r1"][-1] == (4, 1)
    assert plans["r2"][-1] == (0, 1)
    assert any(cell in {(2, 0), (2, 2)} for path in plans.values() for cell in path)


def test_cbs_is_deterministic():
    grid = Grid(5, 5)
    requests = [
        RobotPlanRequest("a", (0, 2), (4, 2)),
        RobotPlanRequest("b", (2, 0), (2, 4)),
        RobotPlanRequest("c", (4, 3), (0, 3)),
    ]
    assert plan_cbs(grid, requests, max_time=25) == plan_cbs(
        grid, list(reversed(requests)), max_time=25
    )


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        plan_cbs(
            Grid(3, 3),
            [
                RobotPlanRequest("r", (0, 0), (1, 0)),
                RobotPlanRequest("r", (2, 0), (1, 0)),
            ],
        )

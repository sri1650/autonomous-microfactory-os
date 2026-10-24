from microfactory.fleet.cooperative import RobotPlanRequest, plan_cooperatively
from microfactory.fleet.grid import Grid


def timed_cells(path, start_time=0):
    return {(cell, start_time + i) for i, cell in enumerate(path)}


def test_cooperative_planner_prevents_vertex_conflicts():
    grid = Grid(3, 2)
    plans, _ = plan_cooperatively(
        grid,
        [
            RobotPlanRequest("r1", (0, 0), (2, 0), priority=10),
            RobotPlanRequest("r2", (2, 0), (0, 0), priority=5),
        ],
        max_time=10,
    )
    assert plans["r1"][-1] == (2, 0)
    assert plans["r2"][-1] == (0, 0)
    assert not (timed_cells(plans["r1"]) & timed_cells(plans["r2"]))


def test_priority_order_is_deterministic():
    grid = Grid(4, 3)
    requests = [
        RobotPlanRequest("z-low", (0, 0), (3, 0), priority=1),
        RobotPlanRequest("a-high", (3, 0), (0, 0), priority=5),
    ]
    first, _ = plan_cooperatively(grid, requests, max_time=12)
    second, _ = plan_cooperatively(grid, list(reversed(requests)), max_time=12)
    assert first == second


def test_planning_failure_does_not_mutate_input_table():
    from microfactory.fleet.reservations import ReservationTable

    grid = Grid(3, 1)
    existing = ReservationTable()
    existing.reserve("fixed", [(1, 0), (1, 0), (1, 0), (1, 0)], 0)
    before_vertices = dict(existing.vertices)
    try:
        plan_cooperatively(
            grid,
            [RobotPlanRequest("r1", (0, 0), (2, 0))],
            reservations=existing,
            max_time=3,
        )
    except ValueError:
        pass
    assert existing.vertices == before_vertices


def test_goal_cell_remains_reserved_through_planning_horizon():
    # r1 stops at (1,0). Without goal holding, r2 would wait one tick and then
    # drive through r1's occupied final cell. The hardened planner must route
    # r2 around via the lower row instead.
    grid = Grid(3, 2)
    plans, table = plan_cooperatively(
        grid,
        [
            RobotPlanRequest("r1", (0, 0), (1, 0), priority=10),
            RobotPlanRequest("r2", (2, 0), (0, 0), priority=5),
        ],
        max_time=10,
    )
    assert plans["r1"][-1] == (1, 0)
    assert (1, 1) in plans["r2"]
    assert all(table.vertices[((1, 0), t)] == "r1" for t in range(1, 11))

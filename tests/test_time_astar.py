import pytest

from microfactory.fleet.grid import Grid
from microfactory.fleet.reservations import ReservationTable
from microfactory.fleet.time_astar import time_astar


def test_time_astar_waits_for_temporarily_reserved_cell():
    grid = Grid(3, 1)
    table = ReservationTable()
    table.reserve("blocker", [(1, 0)], start_time=1)
    path = time_astar(grid, table, "r1", (0, 0), (2, 0), start_time=0, max_time=5)
    assert path == [(0, 0), (0, 0), (1, 0), (2, 0)]


def test_time_astar_avoids_edge_swap():
    grid = Grid(2, 2)
    table = ReservationTable()
    table.reserve("r2", [(1, 0), (0, 0)], start_time=0)
    path = time_astar(grid, table, "r1", (0, 0), (1, 0), start_time=0, max_time=6)
    assert path != [(0, 0), (1, 0)]
    assert path[-1] == (1, 0)


def test_time_astar_is_deterministic():
    grid = Grid(4, 4)
    table = ReservationTable()
    results = [time_astar(grid, table, "r1", (0, 0), (3, 3), max_time=12) for _ in range(10)]
    assert all(path == results[0] for path in results)


def test_time_astar_fails_with_bounded_horizon():
    grid = Grid(3, 1)
    table = ReservationTable()
    table.reserve("blocker", [(1, 0), (1, 0), (1, 0)], start_time=1)
    with pytest.raises(ValueError, match="no time-feasible"):
        time_astar(grid, table, "r1", (0, 0), (2, 0), start_time=0, max_time=3)



def test_goal_must_be_free_for_remaining_horizon():
    grid = Grid(4, 2)
    table = ReservationTable()
    # Existing robot passes through (2, 0) at t=3 then leaves it.
    table.reserve("existing", [(3, 1), (3, 0), (2, 0), (1, 0)], start_time=1)
    path = time_astar(grid, table, "new", (0, 0), (2, 0), max_time=8)
    # The new robot must not simply arrive at t=2 and claim it can stay there.
    # It must delay/re-route until the future occupancy has cleared.
    assert path[-1] == (2, 0)
    assert len(path) - 1 >= 4

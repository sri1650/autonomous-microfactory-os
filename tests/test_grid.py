import pytest

from microfactory.fleet.grid import Grid, astar, path_cost


def test_astar_finds_short_path_around_wall():
    grid = Grid(5, 4, frozenset({(2, 0), (2, 1), (2, 2)}))
    path = astar(grid, (0, 0), (4, 0))
    assert path[0] == (0, 0)
    assert path[-1] == (4, 0)
    assert not (set(path) & grid.blocked)
    assert len(path) == 11
    assert path_cost(path) == 10


def test_astar_tie_breaking_is_deterministic():
    grid = Grid(4, 4)
    results = [astar(grid, (0, 0), (3, 3)) for _ in range(20)]
    assert all(path == results[0] for path in results)


def test_astar_same_cell():
    grid = Grid(2, 2)
    path = astar(grid, (1, 1), (1, 1))
    assert path == [(1, 1)]
    assert path_cost(path) == 0


def test_path_cost_rejects_non_adjacent_steps():
    with pytest.raises(ValueError, match="non-adjacent"):
        path_cost([(0, 0), (2, 0)])


def test_astar_rejects_blocked_goal():
    grid = Grid(2, 2, frozenset({(1, 1)}))
    with pytest.raises(ValueError, match="goal"):
        astar(grid, (0, 0), (1, 1))


def test_astar_reports_unreachable_goal():
    grid = Grid(3, 3, frozenset({(1, 0), (1, 1), (1, 2)}))
    with pytest.raises(ValueError, match="no route"):
        astar(grid, (0, 0), (2, 0))

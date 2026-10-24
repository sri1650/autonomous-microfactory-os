import pytest

from microfactory.fleet.grid import Grid, astar


def test_astar_finds_short_path_around_wall():
    grid = Grid(5, 4, frozenset({(2, 0), (2, 1), (2, 2)}))
    path = astar(grid, (0, 0), (4, 0))
    assert path[0] == (0, 0)
    assert path[-1] == (4, 0)
    assert not (set(path) & grid.blocked)
    assert len(path) == 11


def test_astar_same_cell():
    grid = Grid(2, 2)
    assert astar(grid, (1, 1), (1, 1)) == [(1, 1)]


def test_astar_rejects_blocked_goal():
    grid = Grid(2, 2, frozenset({(1, 1)}))
    with pytest.raises(ValueError, match="goal"):
        astar(grid, (0, 0), (1, 1))


def test_astar_reports_unreachable_goal():
    grid = Grid(3, 3, frozenset({(1, 0), (1, 1), (1, 2)}))
    with pytest.raises(ValueError, match="no route"):
        astar(grid, (0, 0), (2, 0))

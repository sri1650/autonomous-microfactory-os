import pytest

from microfactory.fleet.grid import Grid
from microfactory.sim.world import FactoryWorld, Station


def test_world_move_and_snapshot_are_deterministic():
    world = FactoryWorld(
        Grid(4, 3, frozenset({(2, 2)})),
        robots={"r2": (2, 0), "r1": (0, 0)},
        stations={"s1": Station("s1", (3, 2), "inspection")},
    )
    world.move_robot("r1", (1, 0))
    assert world.snapshot() == {
        "robots": {"r1": [1, 0], "r2": [2, 0]},
        "stations": {"s1": {"cell": [3, 2], "station_type": "inspection"}},
    }


def test_world_rejects_collisions_and_nonadjacent_move():
    world = FactoryWorld(Grid(4, 1), robots={"r1": (0, 0), "r2": (2, 0)})
    with pytest.raises(ValueError, match="adjacent"):
        world.move_robot("r1", (3, 0))
    world.move_robot("r1", (1, 0))
    with pytest.raises(ValueError, match="occupied"):
        world.move_robot("r1", (2, 0))

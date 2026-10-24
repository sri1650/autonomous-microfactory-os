import pytest

from microfactory.fleet.reservations import ReservationTable


def test_vertex_conflict_is_rejected():
    table = ReservationTable()
    table.reserve("r1", [(0, 0), (1, 0), (2, 0)], start_time=0)
    assert not table.can_reserve("r2", [(2, 1), (1, 0)], start_time=0)


def test_edge_swap_conflict_is_rejected():
    table = ReservationTable()
    table.reserve("r1", [(0, 0), (1, 0)], start_time=0)
    assert not table.can_reserve("r2", [(1, 0), (0, 0)], start_time=0)
    with pytest.raises(ValueError):
        table.reserve("r2", [(1, 0), (0, 0)], start_time=0)


def test_wait_action_can_be_reserved():
    table = ReservationTable()
    table.reserve("r1", [(0, 0), (0, 0), (1, 0)])
    assert table.vertices[((0, 0), 0)] == "r1"
    assert table.vertices[((0, 0), 1)] == "r1"
    assert table.edges[((0, 0), (0, 0), 0)] == "r1"


def test_same_robot_can_refresh_own_reservation():
    table = ReservationTable()
    path = [(0, 0), (1, 0)]
    table.reserve("r1", path)
    assert table.can_reserve("r1", path)


def test_release_robot_clears_routes():
    table = ReservationTable()
    table.reserve("r1", [(0, 0), (1, 0)])
    table.release_robot("r1")
    assert table.can_reserve("r2", [(1, 0), (0, 0)])


def test_release_robot_after_preserves_history_and_releases_future():
    table = ReservationTable()
    table.reserve("r1", [(0, 0), (1, 0), (2, 0), (3, 0)], start_time=0)
    table.release_robot_after("r1", from_time=2)
    assert table.vertices[((0, 0), 0)] == "r1"
    assert table.vertices[((1, 0), 1)] == "r1"
    assert ((2, 0), 2) not in table.vertices
    assert ((3, 0), 3) not in table.vertices
    assert ((1, 0), (2, 0), 1) not in table.edges
    assert table.can_reserve("r2", [(2, 0), (3, 0)], start_time=2)


def test_negative_reservation_time_is_rejected():
    table = ReservationTable()
    with pytest.raises(ValueError, match="non-negative"):
        table.can_reserve("r1", [(0, 0)], start_time=-1)

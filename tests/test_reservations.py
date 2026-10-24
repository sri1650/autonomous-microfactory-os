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

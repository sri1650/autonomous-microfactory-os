from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from .grid import Cell, Grid
from .reservations import ReservationTable
from .time_astar import time_astar


@dataclass(frozen=True, slots=True)
class RobotPlanRequest:
    robot_id: str
    start: Cell
    goal: Cell
    priority: int = 0
    start_time: int = 0


def plan_cooperatively(
    grid: Grid,
    requests: list[RobotPlanRequest],
    *,
    reservations: ReservationTable | None = None,
    max_time: int | None = None,
) -> tuple[dict[str, list[Cell]], ReservationTable]:
    """Prioritised cooperative planning with transactional reservation semantics."""
    ids = [request.robot_id for request in requests]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate robot_id in planning request")

    working = deepcopy(reservations) if reservations is not None else ReservationTable()
    plans: dict[str, list[Cell]] = {}
    ordered = sorted(requests, key=lambda request: (-request.priority, request.robot_id))

    for request in ordered:
        path = time_astar(
            grid,
            working,
            request.robot_id,
            request.start,
            request.goal,
            start_time=request.start_time,
            max_time=max_time,
        )
        working.reserve(request.robot_id, path, request.start_time)
        plans[request.robot_id] = path

    return plans, working

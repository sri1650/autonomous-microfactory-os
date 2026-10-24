from __future__ import annotations

from heapq import heappop, heappush
from math import inf

from .grid import Cell, Grid, manhattan
from .reservations import ReservationTable

TimedState = tuple[Cell, int]


def _vertex_free(table: ReservationTable, robot_id: str, cell: Cell, t: int) -> bool:
    owner = table.vertices.get((cell, t))
    return owner is None or owner == robot_id


def _edge_free(
    table: ReservationTable,
    robot_id: str,
    current: Cell,
    nxt: Cell,
    departure_t: int,
) -> bool:
    reverse_owner = table.edges.get((nxt, current, departure_t))
    return reverse_owner is None or reverse_owner == robot_id


def time_astar(
    grid: Grid,
    table: ReservationTable,
    robot_id: str,
    start: Cell,
    goal: Cell,
    *,
    start_time: int = 0,
    max_time: int | None = None,
) -> list[Cell]:
    """A* in (cell,time) space with wait actions and temporal reservations."""
    if start_time < 0:
        raise ValueError("start_time must be non-negative")
    if not grid.passable(start):
        raise ValueError("start is outside the grid or blocked")
    if not grid.passable(goal):
        raise ValueError("goal is outside the grid or blocked")
    if not _vertex_free(table, robot_id, start, start_time):
        raise ValueError("start cell is reserved by another robot")

    if max_time is None:
        # Finite horizon prevents an unreachable temporal problem from waiting forever.
        max_time = start_time + max(20, grid.width * grid.height * 4)
    if max_time < start_time:
        raise ValueError("max_time must be >= start_time")

    start_state: TimedState = (start, start_time)
    # (f, h, time, x, y, insertion_order, state)
    frontier: list[tuple[int, int, int, int, int, int, TimedState]] = []
    counter = 0
    h0 = manhattan(start, goal)
    heappush(frontier, (h0, h0, start_time, start[0], start[1], counter, start_state))
    came_from: dict[TimedState, TimedState | None] = {start_state: None}
    g_score: dict[TimedState, int] = {start_state: 0}
    goal_state: TimedState | None = None

    while frontier:
        _, _, _, _, _, _, state = heappop(frontier)
        current, t = state
        if current == goal:
            # Cooperative planning treats a robot as occupying its goal until
            # a later replanning cycle explicitly releases it. Reaching a goal
            # is therefore only terminal when that cell remains free for the
            # rest of this planning horizon. Otherwise the planner may need to
            # wait elsewhere and enter the goal after an existing route passes.
            if all(
                _vertex_free(table, robot_id, goal, future_t)
                for future_t in range(t, max_time + 1)
            ):
                goal_state = state
                break
        if t >= max_time:
            continue

        candidates = list(grid.neighbors(current)) + [current]  # wait action last
        for nxt in candidates:
            next_t = t + 1
            if not _vertex_free(table, robot_id, nxt, next_t):
                continue
            if not _edge_free(table, robot_id, current, nxt, t):
                continue
            next_state = (nxt, next_t)
            new_g = g_score[state] + 1
            if new_g >= g_score.get(next_state, inf):
                continue
            g_score[next_state] = new_g
            came_from[next_state] = state
            counter += 1
            h = manhattan(nxt, goal)
            heappush(
                frontier,
                (new_g + h, h, next_t, nxt[0], nxt[1], counter, next_state),
            )

    if goal_state is None:
        raise ValueError("no time-feasible route exists within max_time")

    states: list[TimedState] = []
    cursor: TimedState | None = goal_state
    while cursor is not None:
        states.append(cursor)
        cursor = came_from[cursor]
    states.reverse()
    return [cell for cell, _ in states]

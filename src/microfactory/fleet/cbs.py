from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf

from .cooperative import RobotPlanRequest
from .grid import Cell, Grid, manhattan


@dataclass(frozen=True, slots=True)
class VertexConstraint:
    robot_id: str
    cell: Cell
    time: int


@dataclass(frozen=True, slots=True)
class EdgeConstraint:
    robot_id: str
    origin: Cell
    destination: Cell
    time: int  # departure time


Constraint = VertexConstraint | EdgeConstraint


@dataclass(frozen=True, slots=True)
class Conflict:
    time: int
    robot_a: str
    robot_b: str
    kind: str  # "vertex" or "edge"
    cell: Cell | None = None
    a_from: Cell | None = None
    a_to: Cell | None = None
    b_from: Cell | None = None
    b_to: Cell | None = None


def _position(path: list[Cell], time: int) -> Cell:
    if not path:
        raise ValueError("path must not be empty")
    return path[min(time, len(path) - 1)]


def first_conflict(plans: dict[str, list[Cell]]) -> Conflict | None:
    """Return the earliest deterministic vertex or edge conflict.

    Robots are considered to remain at their final cell after arrival. This is
    the standard warehouse assumption unless a later task explicitly releases
    that occupancy.
    """
    if not plans:
        return None
    ids = sorted(plans)
    horizon = max(len(path) for path in plans.values())
    for t in range(horizon):
        for i, left in enumerate(ids):
            a = _position(plans[left], t)
            for right in ids[i + 1 :]:
                b = _position(plans[right], t)
                if a == b:
                    return Conflict(t, left, right, "vertex", cell=a)

        if t + 1 >= horizon:
            continue
        for i, left in enumerate(ids):
            a0 = _position(plans[left], t)
            a1 = _position(plans[left], t + 1)
            for right in ids[i + 1 :]:
                b0 = _position(plans[right], t)
                b1 = _position(plans[right], t + 1)
                if a0 == b1 and a1 == b0 and a0 != a1:
                    return Conflict(
                        t,
                        left,
                        right,
                        "edge",
                        a_from=a0,
                        a_to=a1,
                        b_from=b0,
                        b_to=b1,
                    )
    return None


def _constraints_for(constraints: frozenset[Constraint], robot_id: str):
    vertices: set[tuple[Cell, int]] = set()
    edges: set[tuple[Cell, Cell, int]] = set()
    latest_vertex_by_cell: dict[Cell, int] = {}
    for constraint in constraints:
        if constraint.robot_id != robot_id:
            continue
        if isinstance(constraint, VertexConstraint):
            vertices.add((constraint.cell, constraint.time))
            latest_vertex_by_cell[constraint.cell] = max(
                constraint.time, latest_vertex_by_cell.get(constraint.cell, -1)
            )
        else:
            edges.add((constraint.origin, constraint.destination, constraint.time))
    return vertices, edges, latest_vertex_by_cell


def _low_level_plan(
    grid: Grid,
    request: RobotPlanRequest,
    constraints: frozenset[Constraint],
    *,
    max_time: int,
) -> list[Cell]:
    if request.start_time != 0:
        raise ValueError("CBS currently requires start_time=0 for all robots")
    if not grid.passable(request.start) or not grid.passable(request.goal):
        raise ValueError("start/goal is outside the grid or blocked")

    vertices, edges, latest_vertex = _constraints_for(constraints, request.robot_id)
    if (request.start, 0) in vertices:
        raise ValueError("CBS constraint blocks robot start")

    start = (request.start, 0)
    frontier: list[tuple[int, int, int, int, int, int, tuple[Cell, int]]] = []
    counter = 0
    h0 = manhattan(request.start, request.goal)
    heappush(
        frontier,
        (h0, h0, 0, request.start[0], request.start[1], counter, start),
    )
    came_from: dict[tuple[Cell, int], tuple[Cell, int] | None] = {start: None}
    g_score: dict[tuple[Cell, int], int] = {start: 0}
    goal_state: tuple[Cell, int] | None = None

    while frontier:
        _, _, _, _, _, _, state = heappop(frontier)
        current, t = state
        # Do not terminate at a goal that has a future vertex constraint. Since
        # the robot occupies its goal after arrival, such a plan would remain
        # invalid even though the explicit path list ended.
        if current == request.goal and t > latest_vertex.get(request.goal, -1):
            goal_state = state
            break
        if t >= max_time:
            continue

        candidates = list(grid.neighbors(current)) + [current]
        for nxt in candidates:
            nt = t + 1
            if (nxt, nt) in vertices:
                continue
            if (current, nxt, t) in edges:
                continue
            next_state = (nxt, nt)
            new_g = g_score[state] + 1
            if new_g >= g_score.get(next_state, inf):
                continue
            g_score[next_state] = new_g
            came_from[next_state] = state
            counter += 1
            h = manhattan(nxt, request.goal)
            heappush(frontier, (new_g + h, h, nt, nxt[0], nxt[1], counter, next_state))

    if goal_state is None:
        raise ValueError("no CBS-feasible route exists within max_time")

    path: list[Cell] = []
    cursor: tuple[Cell, int] | None = goal_state
    while cursor is not None:
        path.append(cursor[0])
        cursor = came_from[cursor]
    path.reverse()
    return path


def _sum_of_costs(plans: dict[str, list[Cell]]) -> int:
    return sum(len(path) - 1 for path in plans.values())


def plan_cbs(
    grid: Grid,
    requests: list[RobotPlanRequest],
    *,
    max_time: int | None = None,
    max_high_level_nodes: int = 10_000,
) -> dict[str, list[Cell]]:
    """Conflict-Based Search minimizing sum-of-costs for small/medium fleets.

    This intentionally complements, rather than replaces, the fast prioritised
    cooperative planner. CBS is useful as a quality/reference planner and for
    tightly coupled conflicts where fixed priority order can be suboptimal.
    """
    if max_high_level_nodes <= 0:
        raise ValueError("max_high_level_nodes must be positive")
    ids = [request.robot_id for request in requests]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate robot_id in planning request")
    if not requests:
        return {}
    if any(request.start_time != 0 for request in requests):
        raise ValueError("CBS currently requires start_time=0")
    if max_time is None:
        max_time = max(20, grid.width * grid.height * 4)
    if max_time < 0:
        raise ValueError("max_time must be non-negative")

    request_by_id = {request.robot_id: request for request in requests}
    root_constraints: frozenset[Constraint] = frozenset()
    root_plans = {
        robot_id: _low_level_plan(
            grid, request_by_id[robot_id], root_constraints, max_time=max_time
        )
        for robot_id in sorted(request_by_id)
    }

    # (sum-cost, constraint-count, deterministic-signature, insertion, constraints, plans)
    frontier = []
    insertion = 0

    def signature(constraints: frozenset[Constraint]) -> tuple[str, ...]:
        return tuple(sorted(repr(item) for item in constraints))

    heappush(
        frontier,
        (
            _sum_of_costs(root_plans),
            0,
            signature(root_constraints),
            insertion,
            root_constraints,
            root_plans,
        ),
    )
    visited: set[frozenset[Constraint]] = set()
    expanded = 0

    while frontier:
        _, _, _, _, constraints, plans = heappop(frontier)
        if constraints in visited:
            continue
        visited.add(constraints)
        expanded += 1
        if expanded > max_high_level_nodes:
            raise ValueError("CBS exceeded max_high_level_nodes")

        conflict = first_conflict(plans)
        if conflict is None:
            return plans

        branches: list[tuple[str, Constraint]] = []
        if conflict.kind == "vertex":
            assert conflict.cell is not None
            branches = [
                (
                    conflict.robot_a,
                    VertexConstraint(conflict.robot_a, conflict.cell, conflict.time),
                ),
                (
                    conflict.robot_b,
                    VertexConstraint(conflict.robot_b, conflict.cell, conflict.time),
                ),
            ]
        else:
            assert conflict.a_from is not None and conflict.a_to is not None
            assert conflict.b_from is not None and conflict.b_to is not None
            branches = [
                (
                    conflict.robot_a,
                    EdgeConstraint(
                        conflict.robot_a,
                        conflict.a_from,
                        conflict.a_to,
                        conflict.time,
                    ),
                ),
                (
                    conflict.robot_b,
                    EdgeConstraint(
                        conflict.robot_b,
                        conflict.b_from,
                        conflict.b_to,
                        conflict.time,
                    ),
                ),
            ]

        for robot_id, new_constraint in branches:
            child_constraints = frozenset((*constraints, new_constraint))
            if child_constraints in visited:
                continue
            child_plans = {key: list(value) for key, value in plans.items()}
            try:
                child_plans[robot_id] = _low_level_plan(
                    grid,
                    request_by_id[robot_id],
                    child_constraints,
                    max_time=max_time,
                )
            except ValueError:
                continue
            insertion += 1
            heappush(
                frontier,
                (
                    _sum_of_costs(child_plans),
                    len(child_constraints),
                    signature(child_constraints),
                    insertion,
                    child_constraints,
                    child_plans,
                ),
            )

    raise ValueError("CBS found no conflict-free plan")

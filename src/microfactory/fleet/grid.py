from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf
from typing import Iterable

Cell = tuple[int, int]


@dataclass(frozen=True, slots=True)
class Grid:
    width: int
    height: int
    blocked: frozenset[Cell] = frozenset()

    def contains(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, cell: Cell) -> bool:
        return self.contains(cell) and cell not in self.blocked

    def neighbors(self, cell: Cell) -> Iterable[Cell]:
        x, y = cell
        # Fixed order is intentional; it is part of deterministic benchmark behaviour.
        for nxt in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
            if self.passable(nxt):
                yield nxt


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def path_cost(path: list[Cell]) -> int:
    if not path:
        raise ValueError("path must not be empty")
    for left, right in zip(path, path[1:]):
        if manhattan(left, right) != 1:
            raise ValueError(f"non-adjacent path step: {left} -> {right}")
    return len(path) - 1


def astar(grid: Grid, start: Cell, goal: Cell) -> list[Cell]:
    if not grid.passable(start):
        raise ValueError("start is outside the grid or blocked")
    if not grid.passable(goal):
        raise ValueError("goal is outside the grid or blocked")
    if start == goal:
        return [start]

    # (f_score, h_score, x, y, insertion_counter, cell) makes tie-breaking
    # explicit and reproducible rather than relying on incidental heap order.
    frontier: list[tuple[int, int, int, int, int, Cell]] = []
    counter = 0
    h0 = manhattan(start, goal)
    heappush(frontier, (h0, h0, start[0], start[1], counter, start))
    came_from: dict[Cell, Cell | None] = {start: None}
    cost_so_far: dict[Cell, int] = {start: 0}

    while frontier:
        _, _, _, _, _, current = heappop(frontier)
        if current == goal:
            break
        for nxt in grid.neighbors(current):
            new_cost = cost_so_far[current] + 1
            if new_cost < cost_so_far.get(nxt, inf):
                cost_so_far[nxt] = new_cost
                counter += 1
                h = manhattan(nxt, goal)
                priority = new_cost + h
                heappush(frontier, (priority, h, nxt[0], nxt[1], counter, nxt))
                came_from[nxt] = current

    if goal not in came_from:
        raise ValueError("no route exists")

    path: list[Cell] = []
    current: Cell | None = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

from __future__ import annotations

from dataclasses import dataclass, field

from .grid import Cell


@dataclass(slots=True)
class ReservationTable:
    vertices: dict[tuple[Cell, int], str] = field(default_factory=dict)
    edges: dict[tuple[Cell, Cell, int], str] = field(default_factory=dict)

    def can_reserve(self, robot_id: str, path: list[Cell], start_time: int = 0) -> bool:
        for index, cell in enumerate(path):
            t = start_time + index
            owner = self.vertices.get((cell, t))
            if owner is not None and owner != robot_id:
                return False
            if index == 0:
                continue
            prev = path[index - 1]
            reverse_owner = self.edges.get((cell, prev, t - 1))
            if reverse_owner is not None and reverse_owner != robot_id:
                return False
        return True

    def reserve(self, robot_id: str, path: list[Cell], start_time: int = 0) -> None:
        if not path:
            raise ValueError("path must not be empty")
        if not self.can_reserve(robot_id, path, start_time):
            raise ValueError("reservation conflicts with an existing route")
        for index, cell in enumerate(path):
            t = start_time + index
            self.vertices[(cell, t)] = robot_id
            if index > 0:
                prev = path[index - 1]
                self.edges[(prev, cell, t - 1)] = robot_id

    def release_robot(self, robot_id: str) -> None:
        self.vertices = {key: owner for key, owner in self.vertices.items() if owner != robot_id}
        self.edges = {key: owner for key, owner in self.edges.items() if owner != robot_id}

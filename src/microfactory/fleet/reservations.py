from __future__ import annotations

from dataclasses import dataclass, field

from .grid import Cell


@dataclass(slots=True)
class ReservationTable:
    vertices: dict[tuple[Cell, int], str] = field(default_factory=dict)
    edges: dict[tuple[Cell, Cell, int], str] = field(default_factory=dict)

    def can_reserve(self, robot_id: str, path: list[Cell], start_time: int = 0) -> bool:
        if start_time < 0:
            raise ValueError("start_time must be non-negative")
        for index, cell in enumerate(path):
            t = start_time + index
            owner = self.vertices.get((cell, t))
            if owner is not None and owner != robot_id:
                return False
            if index == 0:
                continue
            prev = path[index - 1]
            # Opposite-direction use of the same edge at the same timestep is
            # an edge-swap collision. Waiting (prev == cell) remains valid.
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

    def release_robot_after(self, robot_id: str, from_time: int) -> None:
        """Release the robot's reservations whose occupancy occurs at/after from_time."""
        if from_time < 0:
            raise ValueError("from_time must be non-negative")
        self.vertices = {
            key: owner
            for key, owner in self.vertices.items()
            if not (owner == robot_id and key[1] >= from_time)
        }
        # Edge key time is departure time; the destination occupancy is t+1.
        self.edges = {
            key: owner
            for key, owner in self.edges.items()
            if not (owner == robot_id and key[2] + 1 >= from_time)
        }

from __future__ import annotations

from dataclasses import dataclass, field

from microfactory.fleet.grid import Cell, Grid, manhattan


@dataclass(frozen=True, slots=True)
class Station:
    station_id: str
    cell: Cell
    station_type: str


@dataclass(slots=True)
class FactoryWorld:
    grid: Grid
    robots: dict[str, Cell] = field(default_factory=dict)
    stations: dict[str, Station] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for robot_id, cell in self.robots.items():
            self._validate_cell(cell, f"robot {robot_id!r}")
        for station_id, station in self.stations.items():
            if station.station_id != station_id:
                raise ValueError("station map key must match station_id")
            self._validate_cell(station.cell, f"station {station_id!r}")
        positions = list(self.robots.values())
        if len(positions) != len(set(positions)):
            raise ValueError("multiple robots cannot occupy the same initial cell")

    def add_robot(self, robot_id: str, cell: Cell) -> None:
        if robot_id in self.robots:
            raise ValueError(f"robot {robot_id!r} already exists")
        self._validate_cell(cell, f"robot {robot_id!r}")
        if cell in self.robots.values():
            raise ValueError("robot cell is already occupied")
        self.robots[robot_id] = cell

    def move_robot(self, robot_id: str, target: Cell) -> None:
        if robot_id not in self.robots:
            raise KeyError(f"unknown robot {robot_id!r}")
        self._validate_cell(target, f"robot {robot_id!r} target")
        current = self.robots[robot_id]
        if manhattan(current, target) > 1:
            raise ValueError("robot move must be adjacent or a wait action")
        if target != current and target in self.robots.values():
            raise ValueError("target cell is occupied by another robot")
        self.robots[robot_id] = target

    def add_station(self, station: Station) -> None:
        if station.station_id in self.stations:
            raise ValueError(f"station {station.station_id!r} already exists")
        self._validate_cell(station.cell, f"station {station.station_id!r}")
        self.stations[station.station_id] = station

    def snapshot(self) -> dict[str, object]:
        return {
            "robots": {key: list(value) for key, value in sorted(self.robots.items())},
            "stations": {
                key: {
                    "cell": list(value.cell),
                    "station_type": value.station_type,
                }
                for key, value in sorted(self.stations.items())
            },
        }

    def _validate_cell(self, cell: Cell, label: str) -> None:
        if not self.grid.passable(cell):
            raise ValueError(f"{label} cell {cell} is outside the grid or blocked")

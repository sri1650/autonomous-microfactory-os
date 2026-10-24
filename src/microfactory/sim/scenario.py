from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from microfactory.fleet.grid import Grid

from .clock import LogicalClock
from .events import SimEvent
from .machines import SimulatedMachine
from .world import FactoryWorld, Station


@dataclass(frozen=True, slots=True)
class MachineSpec:
    machine_id: str
    min_duration_ticks: int
    max_duration_ticks: int
    failure_probability: float = 0.0


@dataclass(frozen=True, slots=True)
class OperationSpec:
    tick: int
    machine_id: str
    task_id: str


@dataclass(frozen=True, slots=True)
class Scenario:
    version: int
    seed: int
    grid: Grid
    robots: tuple[tuple[str, tuple[int, int]], ...]
    stations: tuple[Station, ...]
    machines: tuple[MachineSpec, ...]
    operations: tuple[OperationSpec, ...]


def _cell(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{label} must be [x, y]")
    return int(value[0]), int(value[1])


def scenario_from_dict(raw: dict[str, Any]) -> Scenario:
    if raw.get("version") != 1:
        raise ValueError("unsupported scenario version")
    if "seed" not in raw:
        raise ValueError("scenario seed is required")

    grid_raw = raw.get("grid") or {}
    width = int(grid_raw.get("width", 0))
    height = int(grid_raw.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("grid width/height must be positive")
    blocked = frozenset(_cell(value, "blocked cell") for value in grid_raw.get("blocked", []))
    grid = Grid(width, height, blocked)

    robots_list: list[tuple[str, tuple[int, int]]] = []
    robot_ids: set[str] = set()
    for item in raw.get("robots", []):
        robot_id = str(item["id"])
        if robot_id in robot_ids:
            raise ValueError(f"duplicate robot id {robot_id!r}")
        robot_ids.add(robot_id)
        robots_list.append((robot_id, _cell(item["start"], "robot start")))

    stations_list: list[Station] = []
    station_ids: set[str] = set()
    for item in raw.get("stations", []):
        station_id = str(item["id"])
        if station_id in station_ids:
            raise ValueError(f"duplicate station id {station_id!r}")
        station_ids.add(station_id)
        stations_list.append(Station(station_id, _cell(item["cell"], "station cell"), str(item["type"])))

    machines_list: list[MachineSpec] = []
    machine_ids: set[str] = set()
    for item in raw.get("machines", []):
        machine_id = str(item["id"])
        if machine_id in machine_ids:
            raise ValueError(f"duplicate machine id {machine_id!r}")
        machine_ids.add(machine_id)
        duration = item.get("duration_ticks")
        if not isinstance(duration, (list, tuple)) or len(duration) != 2:
            raise ValueError("machine duration_ticks must be [min,max]")
        machines_list.append(
            MachineSpec(
                machine_id,
                int(duration[0]),
                int(duration[1]),
                float(item.get("failure_probability", 0.0)),
            )
        )

    operations_list: list[OperationSpec] = []
    for item in raw.get("operations", []):
        machine_id = str(item["machine_id"])
        if machine_id not in machine_ids:
            raise ValueError(f"operation references unknown machine {machine_id!r}")
        tick = int(item["tick"])
        if tick < 0:
            raise ValueError("operation tick must be non-negative")
        operations_list.append(OperationSpec(tick, machine_id, str(item["task_id"])))
    operations_list.sort(key=lambda op: (op.tick, op.machine_id, op.task_id))

    scenario = Scenario(
        version=1,
        seed=int(raw["seed"]),
        grid=grid,
        robots=tuple(sorted(robots_list)),
        stations=tuple(sorted(stations_list, key=lambda station: station.station_id)),
        machines=tuple(sorted(machines_list, key=lambda machine: machine.machine_id)),
        operations=tuple(operations_list),
    )
    # Validate physical placement immediately.
    FactoryWorld(grid, dict(scenario.robots), {station.station_id: station for station in scenario.stations})
    return scenario


def load_scenario(path: str | Path) -> Scenario:
    path = Path(path)
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        raw = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to load YAML scenarios") from exc
        raw = yaml.safe_load(text)
    else:
        raise ValueError("scenario file must be JSON or YAML")
    if not isinstance(raw, dict):
        raise ValueError("scenario root must be an object")
    return scenario_from_dict(raw)


def _derived_seed(seed: int, namespace: str) -> int:
    digest = sha256(f"{seed}:{namespace}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def run_scenario(scenario: Scenario, *, max_ticks: int = 10_000) -> list[SimEvent]:
    """Run deterministic machine operations from a versioned scenario."""
    clock = LogicalClock()
    events: list[SimEvent] = []
    sequence = 0

    def emit(kind: str, aggregate_id: str, payload: dict[str, Any]) -> None:
        nonlocal sequence
        sequence += 1
        events.append(SimEvent(clock.now, sequence, kind, aggregate_id, payload))

    world = FactoryWorld(
        scenario.grid,
        dict(scenario.robots),
        {station.station_id: station for station in scenario.stations},
    )
    emit("WORLD_INITIALIZED", "factory", {"seed": scenario.seed, "snapshot": world.snapshot()})

    machines = {
        spec.machine_id: SimulatedMachine(
            spec.machine_id,
            min_duration_ticks=spec.min_duration_ticks,
            max_duration_ticks=spec.max_duration_ticks,
            failure_probability=spec.failure_probability,
            seed=_derived_seed(scenario.seed, spec.machine_id),
        )
        for spec in scenario.machines
    }

    pending = list(scenario.operations)
    while pending or any(machine.task_id is not None for machine in machines.values()):
        if clock.now > max_ticks:
            raise RuntimeError("scenario exceeded max_ticks")

        while pending and pending[0].tick == clock.now:
            operation = pending.pop(0)
            machine = machines[operation.machine_id]
            complete_at = machine.start(operation.task_id, clock.now)
            emit(
                "MACHINE_STARTED",
                operation.machine_id,
                {"task_id": operation.task_id, "complete_at": complete_at},
            )

        for machine_id in sorted(machines):
            completion = machines[machine_id].poll(clock.now)
            if completion is not None:
                emit(
                    "MACHINE_SUCCEEDED" if completion.succeeded else "MACHINE_FAILED",
                    machine_id,
                    {"task_id": completion.task_id},
                )

        if pending or any(machine.task_id is not None for machine in machines.values()):
            clock.advance()

    emit("SCENARIO_COMPLETE", "factory", {"tick": clock.now})
    return events

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import random
from typing import Sequence

from microfactory.fleet.health import RobotTelemetry


class FaultType(str, Enum):
    HEARTBEAT_LOSS="heartbeat_loss"
    MOTOR_OVERTEMP="motor_overtemp"
    BATTERY_DROP="battery_drop"
    SENSOR_FAILURE="sensor_failure"
    COMMUNICATION_BURST="communication_burst"


@dataclass(frozen=True, slots=True)
class Fault:
    tick: int
    resource_id: str
    fault_type: FaultType
    magnitude: float = 1.0


def generate_fault_schedule(
    resource_ids: Sequence[str],
    *,
    seed: int,
    horizon: int,
    count: int,
) -> list[Fault]:
    if not resource_ids:
        raise ValueError("resource_ids cannot be empty")
    if horizon <= 0 or count < 0:
        raise ValueError("invalid horizon/count")
    rng=random.Random(seed)
    types=list(FaultType)
    faults=[]
    for _ in range(count):
        faults.append(Fault(
            tick=rng.randrange(horizon),
            resource_id=rng.choice(list(resource_ids)),
            fault_type=rng.choice(types),
            magnitude=round(rng.uniform(0.5,1.5),3),
        ))
    return sorted(faults,key=lambda f:(f.tick,f.resource_id,f.fault_type.value))


def apply_fault_to_telemetry(t: RobotTelemetry, fault: Fault) -> RobotTelemetry:
    if fault.resource_id != t.robot_id:
        return t
    m=max(0.0,fault.magnitude)
    if fault.fault_type is FaultType.HEARTBEAT_LOSS:
        return replace(t,heartbeat_age_ms=max(t.heartbeat_age_ms,2500*m))
    if fault.fault_type is FaultType.MOTOR_OVERTEMP:
        return replace(t,motor_temp_c=max(t.motor_temp_c,90*m))
    if fault.fault_type is FaultType.BATTERY_DROP:
        return replace(t,battery_pct=max(0.0,t.battery_pct-35*m))
    if fault.fault_type is FaultType.SENSOR_FAILURE:
        return replace(t,sensor_ok=False)
    if fault.fault_type is FaultType.COMMUNICATION_BURST:
        return replace(t,communication_errors=t.communication_errors+int(round(20*m)))
    raise ValueError(f"unknown fault {fault.fault_type}")

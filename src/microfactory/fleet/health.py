from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class HealthState(str, Enum):
    HEALTHY="HEALTHY"
    DEGRADED="DEGRADED"
    FAULTED="FAULTED"
    OFFLINE="OFFLINE"
    RECOVERING="RECOVERING"


@dataclass(frozen=True, slots=True)
class RobotTelemetry:
    robot_id: str
    battery_pct: float
    motor_temp_c: float
    heartbeat_age_ms: float
    communication_errors: int = 0
    sensor_ok: bool = True
    drive_ok: bool = True


@dataclass(frozen=True, slots=True)
class HealthAssessment:
    robot_id: str
    state: HealthState
    reasons: tuple[str, ...]
    score: float


def assess_health(t: RobotTelemetry) -> HealthAssessment:
    reasons=[]
    if t.heartbeat_age_ms >= 2000:
        return HealthAssessment(t.robot_id,HealthState.OFFLINE,("heartbeat_timeout",),0.0)
    if not t.drive_ok:
        return HealthAssessment(t.robot_id,HealthState.FAULTED,("drive_fault",),0.0)

    score=100.0
    if not t.sensor_ok:
        reasons.append("sensor_fault")
        score-=45
    if t.motor_temp_c >= 85:
        reasons.append("motor_overtemp")
        score-=45
    elif t.motor_temp_c >= 70:
        reasons.append("motor_hot")
        score-=20
    if t.battery_pct < 15:
        reasons.append("battery_critical")
        score-=35
    elif t.battery_pct < 30:
        reasons.append("battery_low")
        score-=15
    if t.heartbeat_age_ms >= 500:
        reasons.append("heartbeat_slow")
        score-=20
    if t.communication_errors >= 10:
        reasons.append("communication_errors")
        score-=20

    score=max(0.0,score)
    state=HealthState.HEALTHY if not reasons else HealthState.DEGRADED
    return HealthAssessment(t.robot_id,state,tuple(reasons),score)


def estimated_battery_use_pct(distance_cells: int, *, pct_per_cell: float=0.15, fixed_cost_pct: float=0.5) -> float:
    if distance_cells < 0 or pct_per_cell < 0 or fixed_cost_pct < 0:
        raise ValueError("energy parameters cannot be negative")
    return fixed_cost_pct + distance_cells*pct_per_cell


def can_accept_mission(
    telemetry: RobotTelemetry,
    *,
    distance_cells: int,
    reserve_pct: float=20.0,
) -> bool:
    health=assess_health(telemetry)
    if health.state not in {HealthState.HEALTHY,HealthState.DEGRADED}:
        return False
    if "battery_critical" in health.reasons or "sensor_fault" in health.reasons:
        return False
    required=estimated_battery_use_pct(distance_cells)
    return telemetry.battery_pct-required >= reserve_pct


def choose_robot(
    telemetry: Iterable[RobotTelemetry],
    *,
    distance_by_robot: dict[str,int],
    reserve_pct: float=20.0,
) -> str | None:
    candidates=[]
    for t in telemetry:
        distance=distance_by_robot.get(t.robot_id)
        if distance is None:
            continue
        if not can_accept_mission(t,distance_cells=distance,reserve_pct=reserve_pct):
            continue
        h=assess_health(t)
        projected=t.battery_pct-estimated_battery_use_pct(distance)
        candidates.append((-h.score,-projected,distance,t.robot_id))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]

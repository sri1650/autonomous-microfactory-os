from microfactory.fleet.health import *

def T(**kw):
    base=dict(robot_id="r1",battery_pct=80,motor_temp_c=40,heartbeat_age_ms=20,communication_errors=0,sensor_ok=True,drive_ok=True)
    base.update(kw)
    return RobotTelemetry(**base)

def test_healthy():
    assert assess_health(T()).state is HealthState.HEALTHY

def test_offline_heartbeat():
    assert assess_health(T(heartbeat_age_ms=2500)).state is HealthState.OFFLINE

def test_critical_battery_rejected():
    assert not can_accept_mission(T(battery_pct=10),distance_cells=5)

def test_choose_healthier_robot():
    robots=[T(robot_id="a",battery_pct=45,motor_temp_c=75),T(robot_id="b",battery_pct=70)]
    assert choose_robot(robots,distance_by_robot={"a":2,"b":4})=="b"

def test_long_mission_reserve():
    assert not can_accept_mission(T(battery_pct=25),distance_cells=50,reserve_pct=20)

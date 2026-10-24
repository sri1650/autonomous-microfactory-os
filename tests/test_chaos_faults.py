from microfactory.chaos import *
from microfactory.fleet.health import RobotTelemetry, assess_health, HealthState

def base(robot="r1"):
    return RobotTelemetry(robot,80,40,10)

def test_schedule_is_deterministic():
    assert generate_fault_schedule(["r1","r2"],seed=7,horizon=100,count=10)==generate_fault_schedule(["r1","r2"],seed=7,horizon=100,count=10)

def test_heartbeat_fault_makes_offline():
    t=apply_fault_to_telemetry(base(),Fault(1,"r1",FaultType.HEARTBEAT_LOSS,1.0))
    assert assess_health(t).state is HealthState.OFFLINE

def test_other_robot_unchanged():
    f=Fault(1,"r2",FaultType.BATTERY_DROP,1.0)
    t=base()
    assert apply_fault_to_telemetry(t,f)==t

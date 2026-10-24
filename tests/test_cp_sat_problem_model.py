import pytest
from microfactory.adapters.memory import InMemoryEventSink,InMemoryJobRepository
from microfactory.domain.models import JobRecord,ResourceRecord,ResourceState,TaskDefinition,TaskRecord
from microfactory.orchestrator import Orchestrator
from microfactory.scheduler.cp_sat import build_problem,solve_cp_sat

def prepared():
    job=JobRecord("j",7,{
        "a":TaskRecord(TaskDefinition("a","PRINT","printer",payload={"duration":4,"due_tick":12})),
        "b":TaskRecord(TaskDefinition("b","VISION","vision",dependencies=("a",),payload={"duration":2})),
    })
    svc=Orchestrator(InMemoryJobRepository(),InMemoryEventSink())
    return svc.submit_job(job,command_id="s").job

def test_problem_extracts_dependencies_capacity_priority():
    p=build_problem([prepared()],[
        ResourceRecord("p1","printer"),
        ResourceRecord("p2","printer",state=ResourceState.FAULTED),
        ResourceRecord("v1","vision"),
    ])
    assert p.capacities=={"printer":1,"vision":1}
    b=next(t for t in p.tasks if t.task_id=="b")
    assert b.dependencies==(("j","a"),)
    assert b.priority==7

def test_invalid_duration_rejected():
    job=JobRecord("j",1,{"a":TaskRecord(TaskDefinition("a","X","m",payload={"duration":0}))})
    svc=Orchestrator(InMemoryJobRepository(),InMemoryEventSink())
    ready=svc.submit_job(job,command_id="s").job
    with pytest.raises(ValueError):
        build_problem([ready],[ResourceRecord("m1","m")])

def test_solver_boundary_is_explicit_without_ortools():
    p=build_problem([prepared()],[ResourceRecord("p1","printer"),ResourceRecord("v1","vision")])
    with pytest.raises((RuntimeError,NotImplementedError)):
        solve_cp_sat(p)

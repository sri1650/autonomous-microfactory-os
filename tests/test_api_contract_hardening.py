from fastapi.testclient import TestClient
from apps.factory_api.app import create_app
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.orchestrator import Orchestrator
from microfactory.domain.models import TaskState

def setup():
    repo=InMemoryJobRepository()
    svc=Orchestrator(repo,InMemoryEventSink())
    return TestClient(create_app(svc)),svc

def job_payload():
    return {"job_id":"j1","priority":1,"tasks":[
        {"task_id":"t1","kind":"TEST","required_resource_type":"machine","dependencies":[]}
    ]}

def test_duplicate_command_id_different_operation_rejected():
    c,_=setup()
    assert c.post("/jobs",headers={"X-Command-ID":"cmd"},json=job_payload()).status_code==201
    assert c.post("/jobs/j1/cancel",headers={"X-Command-ID":"cmd"}).status_code==409

def test_retry_endpoint_recovers_failed_task():
    c,svc=setup()
    c.post("/jobs",headers={"X-Command-ID":"create"},json=job_payload())
    svc.transition_task("j1","t1",TaskState.ASSIGNED,command_id="a",resource_id="m1")
    svc.transition_task("j1","t1",TaskState.EXECUTING,command_id="e")
    svc.transition_task("j1","t1",TaskState.FAILED,command_id="f")
    r=c.post("/jobs/j1/tasks/t1/retry",headers={"X-Command-ID":"retry"})
    assert r.status_code==200
    assert r.json()["job"]["state"]=="RUNNING"
    assert r.json()["job"]["tasks"][0]["state"]=="READY"

def test_retry_unknown_job_is_404():
    c,_=setup()
    assert c.post("/jobs/no/tasks/t/retry",headers={"X-Command-ID":"r"}).status_code==404

from fastapi.testclient import TestClient

from apps.factory_api import create_app
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.orchestrator import Orchestrator


def client():
    service = Orchestrator(InMemoryJobRepository(), InMemoryEventSink())
    return TestClient(create_app(service))


def valid_job():
    return {
        "job_id": "job-1",
        "priority": 10,
        "tasks": [
            {
                "task_id": "load",
                "kind": "LOAD",
                "required_resource_type": "gantry",
            },
            {
                "task_id": "move",
                "kind": "MOVE",
                "required_resource_type": "mover",
                "dependencies": ["load"],
            },
        ],
    }


def test_create_get_cancel_job():
    c = client()
    created = c.post("/jobs", json=valid_job(), headers={"X-Command-ID": "create-1"})
    assert created.status_code == 201
    assert created.json()["job"]["state"] == "RUNNING"
    assert created.json()["job"]["tasks"][0]["state"] == "READY"

    fetched = c.get("/jobs/job-1")
    assert fetched.status_code == 200
    assert fetched.json()["job_id"] == "job-1"

    cancelled = c.post("/jobs/job-1/cancel", headers={"X-Command-ID": "cancel-1"})
    assert cancelled.status_code == 200
    assert cancelled.json()["job"]["state"] == "CANCELLED"


def test_create_is_idempotent_for_same_command_id():
    c = client()
    first = c.post("/jobs", json=valid_job(), headers={"X-Command-ID": "same"})
    second = c.post("/jobs", json=valid_job(), headers={"X-Command-ID": "same"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["replayed"] is True


def test_duplicate_task_ids_are_rejected_at_boundary():
    c = client()
    body = valid_job()
    body["tasks"].append(dict(body["tasks"][0]))
    response = c.post("/jobs", json=body, headers={"X-Command-ID": "dup"})
    assert response.status_code == 422


def test_missing_job_returns_404():
    c = client()
    assert c.get("/jobs/missing").status_code == 404

from fastapi.testclient import TestClient
from apps.factory_api.app import create_app
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.orchestrator import Orchestrator

def client():
    return TestClient(create_app(Orchestrator(InMemoryJobRepository(),InMemoryEventSink())))

def test_dashboard_renders():
    r=client().get("/dashboard")
    assert r.status_code==200
    assert "AUTONOMOUS MICROFACTORY OS" in r.text
    assert "SIMULATION PREVIEW" in r.text

def test_demo_snapshot_has_jobs_and_robots():
    data=client().get("/demo/snapshot").json()
    assert data["mode"]=="simulation-preview"
    assert data["jobs"] and data["robots"]

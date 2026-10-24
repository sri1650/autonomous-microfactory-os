from fastapi.testclient import TestClient
from apps.factory_api.app import create_app
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.orchestrator import Orchestrator

def c():
    return TestClient(create_app(Orchestrator(InMemoryJobRepository(),InMemoryEventSink())))

def test_time_machine_page():
    r=c().get("/time-machine")
    assert r.status_code==200
    assert "Factory Time Machine" in r.text
    assert "deterministic replay" in r.text

def test_replay_preview_has_failure_and_recovery():
    frames=c().get("/demo/replay").json()["frames"]
    assert any("FAILED" in f["summary"] for f in frames)
    assert any("attempt=2" in f["summary"] for f in frames)

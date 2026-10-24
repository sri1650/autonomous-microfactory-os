from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from apps.factory_api import create_app
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.orchestrator import Orchestrator
from microfactory.telemetry import TracingEventSink, start_job_span


def make_tracer():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider.get_tracer("microfactory-tests"), exporter, provider


def test_event_sink_captures_current_trace_identity():
    tracer, exporter, provider = make_tracer()
    inner = InMemoryEventSink()
    sink = TracingEventSink(inner)
    with start_job_span(tracer, "job.submit", job_id="job-1", command_id="cmd-1"):
        sink.append(event_type="TEST", aggregate_id="job-1", payload={"x": 1})
    provider.force_flush()

    event = inner.events[0]
    assert event.payload["correlation_id"] == "job-1"
    assert len(event.payload["trace_id"]) == 32
    assert len(event.payload["span_id"]) == 16
    assert len(exporter.get_finished_spans()) == 1


def test_factory_api_span_correlates_orchestrator_event():
    tracer, exporter, provider = make_tracer()
    raw_events = InMemoryEventSink()
    service = Orchestrator(InMemoryJobRepository(), TracingEventSink(raw_events))
    client = TestClient(create_app(service, tracer=tracer))

    response = client.post(
        "/jobs",
        headers={"X-Command-ID": "cmd-create"},
        json={
            "job_id": "job-42",
            "priority": 1,
            "tasks": [
                {
                    "task_id": "inspect",
                    "kind": "INSPECT",
                    "required_resource_type": "vision",
                }
            ],
        },
    )
    assert response.status_code == 201
    provider.force_flush()

    event = raw_events.events[0]
    assert event.aggregate_id == "job-42"
    assert event.payload["correlation_id"] == "job-42"
    assert len(event.payload["trace_id"]) == 32
    spans = exporter.get_finished_spans()
    assert any(span.name == "POST /jobs" for span in spans)

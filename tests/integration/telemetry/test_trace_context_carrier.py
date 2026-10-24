from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from microfactory.telemetry.tracing import inject_trace_context,extract_trace_context

def test_w3c_trace_context_round_trip():
    provider=TracerProvider()
    tracer=provider.get_tracer("test")
    with tracer.start_as_current_span("parent") as span:
        carrier=inject_trace_context()
        assert "traceparent" in carrier
        context=extract_trace_context(carrier)
        child=tracer.start_span("child",context=context)
        try:
            assert child.get_span_context().trace_id==span.get_span_context().trace_id
        finally:
            child.end()

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Tracer

from microfactory.domain.repositories import EventSink


@dataclass(frozen=True, slots=True)
class TraceIdentity:
    trace_id: str
    span_id: str


def current_trace_identity() -> TraceIdentity | None:
    context = trace.get_current_span().get_span_context()
    if not context.is_valid:
        return None
    return TraceIdentity(
        trace_id=f"{context.trace_id:032x}",
        span_id=f"{context.span_id:016x}",
    )


class TracingEventSink:
    """Decorate an EventSink with correlation and current trace identity."""

    def __init__(self, inner: EventSink) -> None:
        self._inner = inner

    def append(
        self,
        *,
        event_type: str,
        aggregate_id: str,
        payload: Mapping[str, Any],
    ) -> None:
        enriched = dict(payload)
        enriched.setdefault("correlation_id", aggregate_id)
        identity = current_trace_identity()
        if identity is not None:
            enriched.setdefault("trace_id", identity.trace_id)
            enriched.setdefault("span_id", identity.span_id)
        self._inner.append(
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=enriched,
        )


def start_job_span(
    tracer: Tracer,
    name: str,
    *,
    job_id: str | None = None,
    command_id: str | None = None,
):
    attributes: dict[str, str] = {}
    if job_id is not None:
        attributes["microfactory.job_id"] = job_id
    if command_id is not None:
        attributes["microfactory.command_id"] = command_id
    return tracer.start_as_current_span(name, attributes=attributes)


def inject_trace_context(carrier: dict[str,str] | None = None) -> dict[str,str]:
    """Inject current W3C trace context into a string carrier for RPC metadata."""
    from opentelemetry.propagate import inject
    out={} if carrier is None else dict(carrier)
    inject(out)
    return out


def extract_trace_context(carrier: Mapping[str,str]):
    """Extract W3C trace context for a downstream Python/Rust RPC boundary."""
    from opentelemetry.propagate import extract
    return extract(dict(carrier))

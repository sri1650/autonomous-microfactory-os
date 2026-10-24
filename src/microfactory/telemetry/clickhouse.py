from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol, Sequence


class ClickHouseInsertClient(Protocol):
    def insert(
        self,
        table: str,
        data: Sequence[Sequence[Any]],
        *,
        column_names: Sequence[str],
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class TelemetryRecord:
    timestamp_ns: int
    event_type: str
    aggregate_id: str
    correlation_id: str
    trace_id: str | None
    span_id: str | None
    payload: dict[str, Any]


class ClickHouseTelemetrySink:
    """Thin injectable boundary around a ClickHouse client.

    The real network client is intentionally supplied by composition. Unit tests
    can verify schema/serialization without needing a ClickHouse server.
    """

    COLUMNS = (
        "timestamp_ns",
        "event_type",
        "aggregate_id",
        "correlation_id",
        "trace_id",
        "span_id",
        "payload_json",
    )

    def __init__(self, client: ClickHouseInsertClient, table: str = "robotics_events") -> None:
        if not table or any(ch.isspace() for ch in table):
            raise ValueError("invalid ClickHouse table name")
        self._client = client
        self._table = table

    def write(self, records: Sequence[TelemetryRecord]) -> None:
        if not records:
            return
        rows = [
            (
                int(record.timestamp_ns),
                record.event_type,
                record.aggregate_id,
                record.correlation_id,
                record.trace_id or "",
                record.span_id or "",
                json.dumps(record.payload, sort_keys=True, separators=(",", ":")),
            )
            for record in records
        ]
        self._client.insert(self._table, rows, column_names=self.COLUMNS)

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol, Sequence


def _text(value: Any) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)


class ClickHouseInsertClient(Protocol):
    def insert(
        self,
        table: str,
        data: Sequence[Sequence[Any]],
        *,
        column_names: Sequence[str],
    ) -> Any: ...

    def query(self, query: str, *, parameters: dict[str, Any] | None = None) -> Any: ...


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

    @classmethod
    def connect(
        cls,
        *,
        host: str = "127.0.0.1",
        port: int = 8123,
        database: str = "default",
        username: str = "default",
        password: str = "",
        table: str = "robotics_events",
    ) -> "ClickHouseTelemetrySink":
        try:
            import clickhouse_connect
        except ImportError as exc:
            raise RuntimeError("clickhouse-connect is required for live telemetry") from exc
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
        )
        return cls(client, table)

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

    def query_correlation(self, correlation_id: str) -> list[TelemetryRecord]:
        result = self._client.query(
            f"""SELECT {', '.join(self.COLUMNS)}
                FROM {self._table}
                WHERE correlation_id = {{correlation_id:String}}
                ORDER BY timestamp_ns, event_type""",
            parameters={"correlation_id": correlation_id},
        )
        return [
            TelemetryRecord(
                timestamp_ns=int(row[0]),
                event_type=str(row[1]),
                aggregate_id=str(row[2]),
                correlation_id=str(row[3]),
                trace_id=_text(row[4]) or None,
                span_id=_text(row[5]) or None,
                payload=json.loads(row[6]),
            )
            for row in result.result_rows
        ]

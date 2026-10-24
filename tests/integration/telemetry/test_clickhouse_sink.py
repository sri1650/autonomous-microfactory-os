import json

from microfactory.telemetry import ClickHouseTelemetrySink, TelemetryRecord


class FakeClient:
    def __init__(self):
        self.calls = []

    def insert(self, table, data, *, column_names):
        self.calls.append((table, list(data), tuple(column_names)))


def test_clickhouse_sink_serializes_deterministically():
    client = FakeClient()
    sink = ClickHouseTelemetrySink(client)
    sink.write(
        [
            TelemetryRecord(
                timestamp_ns=123,
                event_type="TASK_STATE_CHANGED",
                aggregate_id="job-1",
                correlation_id="job-1",
                trace_id="a" * 32,
                span_id="b" * 16,
                payload={"z": 2, "a": 1},
            )
        ]
    )
    assert len(client.calls) == 1
    table, rows, columns = client.calls[0]
    assert table == "robotics_events"
    assert columns[-1] == "payload_json"
    assert rows[0][-1] == '{"a":1,"z":2}'


def test_clickhouse_sink_noops_empty_batch():
    client = FakeClient()
    ClickHouseTelemetrySink(client).write([])
    assert client.calls == []

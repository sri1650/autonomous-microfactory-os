from microfactory.telemetry import ClickHouseTelemetrySink, TelemetryRecord


def test_live_clickhouse_write_and_correlation_query(clickhouse_settings):
    sink = ClickHouseTelemetrySink.connect(**clickhouse_settings)
    sink.write(
        [
            TelemetryRecord(
                timestamp_ns=20,
                event_type="RUNTIME_ACCEPTED",
                aggregate_id="job-live",
                correlation_id="corr-live",
                trace_id="a" * 32,
                span_id="b" * 16,
                payload={"command_id": "cmd-1"},
            ),
            TelemetryRecord(
                timestamp_ns=10,
                event_type="JOB_SUBMITTED",
                aggregate_id="job-live",
                correlation_id="corr-live",
                trace_id="a" * 32,
                span_id="c" * 16,
                payload={"priority": 5},
            ),
            TelemetryRecord(
                timestamp_ns=30,
                event_type="OTHER_JOB",
                aggregate_id="job-other",
                correlation_id="corr-other",
                trace_id="d" * 32,
                span_id="e" * 16,
                payload={},
            ),
        ]
    )

    records = sink.query_correlation("corr-live")
    assert [record.event_type for record in records] == ["JOB_SUBMITTED", "RUNTIME_ACCEPTED"]
    assert {record.trace_id for record in records} == {"a" * 32}
    assert records[1].payload == {"command_id": "cmd-1"}

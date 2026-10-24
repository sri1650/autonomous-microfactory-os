CREATE TABLE IF NOT EXISTS robotics_events
(
    timestamp_ns UInt64,
    event_type LowCardinality(String),
    aggregate_id String,
    correlation_id String,
    trace_id FixedString(32),
    span_id FixedString(16),
    payload_json String
)
ENGINE = MergeTree
ORDER BY (correlation_id, timestamp_ns, event_type);

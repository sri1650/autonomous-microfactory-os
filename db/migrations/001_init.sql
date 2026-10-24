BEGIN;

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    priority INTEGER NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('QUEUED','PLANNING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    required_resource_type TEXT NOT NULL,
    dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    state TEXT NOT NULL CHECK (state IN ('PENDING','READY','ASSIGNED','EXECUTING','SUCCEEDED','FAILED','CANCELLED')),
    attempt INTEGER NOT NULL DEFAULT 0 CHECK (attempt >= 0),
    assigned_resource_id TEXT NULL,
    PRIMARY KEY (job_id, task_id)
);

CREATE TABLE IF NOT EXISTS resources (
    resource_id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('OFFLINE','AVAILABLE','RESERVED','BUSY','FAULTED')),
    capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS command_idempotency (
    command_id TEXT PRIMARY KEY,
    operation_fingerprint TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS domain_events (
    event_id BIGSERIAL PRIMARY KEY,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    correlation_id TEXT NULL,
    trace_id TEXT NULL,
    span_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_state_resource_type
    ON tasks(state, required_resource_type);
CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate
    ON domain_events(aggregate_id, event_id);

COMMIT;

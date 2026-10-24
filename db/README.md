# Persistence preparation

`migrations/001_init.sql` defines the transactional PostgreSQL model for jobs, tasks, resources, durable command idempotency and domain events.

The migration is prepared but **not yet validated against a live PostgreSQL server in this environment**. Work/Codex should run it in an ephemeral PostgreSQL container, implement the repository adapter with psycopg, and add restart/idempotency integration tests before marking M7-T01 complete.

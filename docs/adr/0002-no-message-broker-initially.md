# ADR 0002: No Message Broker Initially

## Status
Accepted.

## Decision
Do not introduce Kafka/NATS/RabbitMQ in the first implementation.

## Why
The system can demonstrate idempotency, tracing, persistence and replay without another distributed component. A broker is added only after a measured throughput/fan-out/reliability need appears.

## Consequences
- In-process Python calls are allowed within one deployment unit.
- gRPC is used at the runtime boundary.
- Durable business state belongs in PostgreSQL; high-volume telemetry belongs in ClickHouse.

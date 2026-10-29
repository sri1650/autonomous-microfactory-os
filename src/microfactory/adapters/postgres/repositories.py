from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable, Protocol, Any

from microfactory.domain.models import JobRecord
from .codec import job_from_rows,job_to_rows


class CursorLike(Protocol):
    def execute(self, query: str, params: tuple | None = None) -> Any: ...
    def fetchone(self): ...
    def fetchall(self): ...
    def __enter__(self): ...
    def __exit__(self,*args): ...


class ConnectionLike(Protocol):
    def cursor(self) -> CursorLike: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class PostgresJobRepository:
    """DB-API-style PostgreSQL adapter with dependency-injected connections.

    Connections are injected for unit tests and can be created from a psycopg
    DSN for live integration.
    """

    def __init__(self, connection_factory: Callable[[], ConnectionLike]) -> None:
        self._connection_factory=connection_factory

    @classmethod
    def from_dsn(cls, dsn: str) -> "PostgresJobRepository":
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL integration") from exc
        return cls(lambda: psycopg.connect(dsn))

    def get(self, job_id: str) -> JobRecord | None:
        conn=self._connection_factory()
        with conn.cursor() as cur:
            cur.execute("SELECT job_id, priority, state FROM jobs WHERE job_id = %s",(job_id,))
            job_row=cur.fetchone()
            if job_row is None:
                return None
            cur.execute(
                """SELECT job_id, task_id, kind, required_resource_type, dependencies, payload,
                          state, attempt, assigned_resource_id
                   FROM tasks WHERE job_id = %s ORDER BY task_id""",
                (job_id,),
            )
            task_rows=cur.fetchall()
        return job_from_rows(job_row,task_rows)

    def save(self, job: JobRecord) -> None:
        job_row,task_rows=job_to_rows(job)
        conn=self._connection_factory()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO jobs(job_id,priority,state)
                       VALUES (%s,%s,%s)
                       ON CONFLICT(job_id) DO UPDATE SET
                         priority=EXCLUDED.priority,
                         state=EXCLUDED.state,
                         version=jobs.version+1,
                         updated_at=NOW()""",
                    job_row,
                )
                cur.execute("DELETE FROM tasks WHERE job_id = %s",(job.job_id,))
                for row in task_rows:
                    db_row=(
                        row[0],row[1],row[2],row[3],
                        json.dumps(row[4]),json.dumps(row[5]),
                        row[6],row[7],row[8],
                    )
                    cur.execute(
                        """INSERT INTO tasks(
                             job_id,task_id,kind,required_resource_type,dependencies,payload,
                             state,attempt,assigned_resource_id
                           ) VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)""",
                        db_row,
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


class PostgresCommandRepository:
    """Durable command-id idempotency records."""

    def __init__(self, connection_factory: Callable[[], ConnectionLike]) -> None:
        self._connection_factory=connection_factory

    @classmethod
    def from_dsn(cls, dsn: str) -> "PostgresCommandRepository":
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL integration") from exc
        return cls(lambda: psycopg.connect(dsn))

    def record(
        self,
        command_id: str,
        operation_fingerprint: str,
        aggregate_id: str,
        result: dict,
    ) -> dict:
        conn = self._connection_factory()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO command_idempotency(
                           command_id, operation_fingerprint, aggregate_id, result_json
                       ) VALUES (%s, %s, %s, %s::jsonb)
                       ON CONFLICT(command_id) DO NOTHING""",
                    (command_id, operation_fingerprint, aggregate_id, json.dumps(result)),
                )
                cur.execute(
                    """SELECT operation_fingerprint, aggregate_id, result_json
                       FROM command_idempotency WHERE command_id = %s""",
                    (command_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError("command idempotency record was not persisted")
                fingerprint = row[0] if not hasattr(row, "keys") else row["operation_fingerprint"]
                stored_aggregate = row[1] if not hasattr(row, "keys") else row["aggregate_id"]
                stored_result = row[2] if not hasattr(row, "keys") else row["result_json"]
                if fingerprint != operation_fingerprint or stored_aggregate != aggregate_id:
                    raise ValueError("command_id was reused for a different operation")
            conn.commit()
            return dict(stored_result)
        except Exception:
            conn.rollback()
            raise


@dataclass(frozen=True, slots=True)
class PersistedDomainEvent:
    event_id: int
    event_type: str
    aggregate_id: str
    payload: dict


class PostgresEventStore:
    """Durable append/read boundary used by orchestration and the live API."""

    def __init__(self, connection_factory: Callable[[], ConnectionLike]) -> None:
        self._connection_factory = connection_factory

    @classmethod
    def from_dsn(cls, dsn: str) -> "PostgresEventStore":
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL integration") from exc
        return cls(lambda: psycopg.connect(dsn))

    def append(self, *, event_type: str, aggregate_id: str, payload) -> None:
        conn = self._connection_factory()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO domain_events(aggregate_id, event_type, payload)
                       VALUES (%s, %s, %s::jsonb)""",
                    (aggregate_id, event_type, json.dumps(dict(payload))),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def list_for_aggregate(self, aggregate_id: str) -> tuple[PersistedDomainEvent, ...]:
        conn = self._connection_factory()
        with conn.cursor() as cur:
            cur.execute(
                """SELECT event_id, event_type, aggregate_id, payload
                   FROM domain_events WHERE aggregate_id = %s ORDER BY event_id""",
                (aggregate_id,),
            )
            rows = cur.fetchall()
        return tuple(
            PersistedDomainEvent(
                event_id=int(row[0]), event_type=str(row[1]), aggregate_id=str(row[2]),
                payload=dict(row[3]),
            )
            for row in rows
        )

from __future__ import annotations

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

    The SQL/serialization boundary is unit tested here. M7-T01 still requires
    live psycopg + PostgreSQL container restart/idempotency tests.
    """

    def __init__(self, connection_factory: Callable[[], ConnectionLike]) -> None:
        self._connection_factory=connection_factory

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

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

from microfactory.domain.models import JobRecord, TaskDefinition, TaskRecord


def parse_job_spec(raw: dict[str, Any]) -> JobRecord:
    if not isinstance(raw, dict):
        raise ValueError("job spec must be a mapping")
    job_id = str(raw.get("job") or raw.get("job_id") or "").strip()
    if not job_id:
        raise ValueError("job/job_id is required")
    priority = int(raw.get("priority", 0))
    raw_tasks = raw.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("tasks must be a non-empty list")

    tasks: dict[str, TaskRecord] = {}
    for item in raw_tasks:
        if not isinstance(item, dict):
            raise ValueError("each task must be a mapping")
        task_id = str(item.get("id") or item.get("task_id") or "").strip()
        if not task_id:
            raise ValueError("task id is required")
        if task_id in tasks:
            raise ValueError(f"duplicate task id {task_id!r}")
        kind = str(item.get("kind") or item.get("type") or task_id).upper()
        resource = str(item.get("resource") or item.get("required_resource_type") or "").strip()
        if not resource:
            raise ValueError(f"task {task_id!r} requires resource")
        deps = item.get("depends_on", item.get("dependencies", []))
        if isinstance(deps, str):
            deps = [deps]
        if not isinstance(deps, list):
            raise ValueError("depends_on must be a list or string")

        reserved = {
            "id","task_id","kind","type","resource","required_resource_type",
            "depends_on","dependencies"
        }
        payload = dict(item.get("payload", {}))
        for key, value in item.items():
            if key not in reserved and key != "payload":
                payload.setdefault(key, value)

        tasks[task_id] = TaskRecord(TaskDefinition(
            task_id=task_id,
            kind=kind,
            required_resource_type=resource,
            dependencies=tuple(str(x) for x in deps),
            payload=payload,
        ))
    job = JobRecord(job_id=job_id, priority=priority, tasks=tasks)
    job.validate_dag()
    return job


def load_job_spec(path: str | Path) -> JobRecord:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return parse_job_spec(raw)

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from microfactory.domain.models import JobRecord, TaskDefinition, TaskRecord
from microfactory.orchestrator import Orchestrator


class TaskInput(BaseModel):
    task_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    required_resource_type: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


class JobInput(BaseModel):
    job_id: str = Field(min_length=1)
    priority: int = 0
    tasks: list[TaskInput]


def _job_payload(job: JobRecord) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "priority": job.priority,
        "state": job.state.value,
        "tasks": [
            {
                "task_id": task.definition.task_id,
                "kind": task.definition.kind,
                "required_resource_type": task.definition.required_resource_type,
                "dependencies": list(task.definition.dependencies),
                "payload": task.definition.payload,
                "state": task.state.value,
                "attempt": task.attempt,
                "assigned_resource_id": task.assigned_resource_id,
            }
            for _, task in sorted(job.tasks.items())
        ],
    }


def create_app(orchestrator: Orchestrator) -> FastAPI:
    app = FastAPI(title="Autonomous Microfactory Factory API", version="0.1.0")

    @app.post("/jobs", status_code=status.HTTP_201_CREATED)
    def create_job(body: JobInput, x_command_id: str = Header(alias="X-Command-ID")):
        if len({task.task_id for task in body.tasks}) != len(body.tasks):
            raise HTTPException(status_code=422, detail="duplicate task_id")
        job = JobRecord(
            job_id=body.job_id,
            priority=body.priority,
            tasks={
                task.task_id: TaskRecord(
                    TaskDefinition(
                        task.task_id,
                        task.kind,
                        task.required_resource_type,
                        tuple(task.dependencies),
                        dict(task.payload),
                    )
                )
                for task in body.tasks
            },
        )
        try:
            result = orchestrator.submit_job(job, command_id=x_command_id)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"replayed": result.replayed, "job": _job_payload(result.job)}

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str):
        try:
            job = orchestrator.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _job_payload(job)

    @app.post("/jobs/{job_id}/cancel")
    def cancel_job(job_id: str, x_command_id: str = Header(alias="X-Command-ID")):
        try:
            result = orchestrator.cancel_job(job_id, command_id=x_command_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"replayed": result.replayed, "job": _job_payload(result.job)}

    return app

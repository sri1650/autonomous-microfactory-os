from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from microfactory.domain.models import JobRecord, TaskDefinition, TaskRecord
from microfactory.orchestrator import Orchestrator
from apps.factory_api.dashboard import dashboard_html, demo_snapshot
from apps.factory_api.time_machine import demo_replay, time_machine_html


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


def create_app(orchestrator: Orchestrator, *, tracer=None, event_reader=None) -> FastAPI:
    app = FastAPI(title="Autonomous Microfactory Factory API", version="0.1.0")

    if tracer is not None:
        @app.middleware("http")
        async def trace_request(request: Request, call_next):
            with tracer.start_as_current_span(
                f"{request.method} {request.url.path}",
                attributes={
                    "http.request.method": request.method,
                    "url.path": request.url.path,
                },
            ) as span:
                response = await call_next(request)
                span.set_attribute("http.response.status_code", response.status_code)
                return response

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "service": "factory-api", "version": "0.1.0"}

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard():
        return dashboard_html()

    @app.get("/demo/snapshot")
    def demo_snapshot_endpoint():
        return demo_snapshot()

    @app.get("/time-machine", response_class=HTMLResponse)
    def time_machine():
        return time_machine_html()

    @app.get("/demo/replay")
    def demo_replay_endpoint():
        return demo_replay()

    @app.get("/capabilities")
    def capabilities():
        return {
            "implemented": [
                "job_orchestration",
                "deterministic_simulation",
                "cooperative_fleet_planning",
                "cbs_reference_planner",
                "vision_verification",
                "deterministic_replay_core",
            ],
            "prepared_not_live_validated": [
                "postgresql_persistence",
                "clickhouse_telemetry",
                "rust_robot_runtime",
                "cp_sat_scheduler",
            ],
            "hardware_validated": False,
        }

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

    if event_reader is not None:
        @app.get("/jobs/{job_id}/events")
        def get_job_events(job_id: str):
            try:
                orchestrator.get_job(job_id)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return {
                "job_id": job_id,
                "events": [
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "payload": event.payload,
                    }
                    for event in event_reader.list_for_aggregate(job_id)
                ],
            }

    @app.post("/jobs/{job_id}/tasks/{task_id}/retry")
    def retry_task(job_id: str, task_id: str, x_command_id: str = Header(alias="X-Command-ID")):
        try:
            result = orchestrator.retry_task(job_id, task_id, command_id=x_command_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"replayed": result.replayed, "job": _job_payload(result.job)}

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

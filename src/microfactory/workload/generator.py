from __future__ import annotations
import random
from microfactory.domain.models import JobRecord, ResourceRecord, TaskDefinition, TaskRecord


def generate_chain_job(job_id: str, *, seed: int, task_count: int=5) -> JobRecord:
    if task_count <= 0:
        raise ValueError("task_count must be positive")
    rng=random.Random(seed)
    types=["mover","vision","gantry","printer"]
    tasks={}
    prev=None
    for i in range(task_count):
        tid=f"t{i:02d}"
        resource=rng.choice(types)
        deps=(prev,) if prev else ()
        tasks[tid]=TaskRecord(TaskDefinition(
            tid,resource.upper(),resource,deps,
            {"duration":rng.randint(1,10),"due_tick":rng.randint(20,100)}
        ))
        prev=tid
    job=JobRecord(job_id,rng.randint(0,10),tasks)
    job.validate_dag()
    return job


def generate_resources(*, per_type: int=2):
    if per_type <= 0:
        raise ValueError("per_type must be positive")
    return [
        ResourceRecord(f"{kind}-{i+1}",kind)
        for kind in ("mover","vision","gantry","printer")
        for i in range(per_type)
    ]

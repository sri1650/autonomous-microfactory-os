from __future__ import annotations

from microfactory.domain.models import JobRecord,JobState,TaskDefinition,TaskRecord,TaskState


def job_to_rows(job: JobRecord):
    job.validate_dag()
    job_row=(job.job_id,job.priority,job.state.value)
    task_rows=[]
    for task_id,record in sorted(job.tasks.items()):
        task_rows.append((
            job.job_id,
            task_id,
            record.definition.kind,
            record.definition.required_resource_type,
            list(record.definition.dependencies),
            dict(record.definition.payload),
            record.state.value,
            record.attempt,
            record.assigned_resource_id,
        ))
    return job_row,task_rows


def job_from_rows(job_row, task_rows):
    if job_row is None:
        return None
    # Accept tuple or mapping-shaped DB rows.
    def get(row,key,index):
        return row[key] if hasattr(row,"keys") else row[index]
    job_id=str(get(job_row,"job_id",0))
    priority=int(get(job_row,"priority",1))
    state=JobState(str(get(job_row,"state",2)))
    tasks={}
    for row in task_rows:
        task_id=str(get(row,"task_id",1))
        dependencies=tuple(get(row,"dependencies",4) or ())
        payload=dict(get(row,"payload",5) or {})
        tasks[task_id]=TaskRecord(
            TaskDefinition(
                task_id,
                str(get(row,"kind",2)),
                str(get(row,"required_resource_type",3)),
                dependencies,
                payload,
            ),
            state=TaskState(str(get(row,"state",6))),
            attempt=int(get(row,"attempt",7)),
            assigned_resource_id=get(row,"assigned_resource_id",8),
        )
    job=JobRecord(job_id,priority,tasks,state)
    job.validate_dag()
    return job

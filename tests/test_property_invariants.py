from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.domain.models import TaskState
from microfactory.orchestrator import Orchestrator
from microfactory.scheduler.heuristics import Heuristic, schedule_heuristic
from microfactory.workload import generate_chain_job, generate_resources


def test_100_generated_jobs_preserve_dag_and_scheduler_invariants():
    resources=generate_resources(per_type=3)
    for seed in range(100):
        original=generate_chain_job(f"j{seed}",seed=seed,task_count=5)
        repo=InMemoryJobRepository()
        svc=Orchestrator(repo,InMemoryEventSink())
        job=svc.submit_job(original,command_id=f"s:{seed}").job
        ready=[tid for tid,t in job.tasks.items() if t.state is TaskState.READY]
        assert ready==["t00"]
        assignments=schedule_heuristic([job],resources,strategy=Heuristic.WEIGHTED)
        assert len(assignments)<=1
        if assignments:
            a=assignments[0]
            task=job.tasks[a.task_id]
            assert task.state is TaskState.READY
            resource=next(r for r in resources if r.resource_id==a.resource_id)
            assert resource.resource_type==task.definition.required_resource_type

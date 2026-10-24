from microfactory.domain.models import JobRecord, ResourceRecord, TaskDefinition, TaskRecord
from microfactory.orchestrator import Orchestrator
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.scheduler.heuristics import Heuristic, schedule_heuristic


def _submit(job):
    repo=InMemoryJobRepository()
    svc=Orchestrator(repo,InMemoryEventSink())
    return svc.submit_job(job,command_id=f"submit:{job.job_id}").job


def _job(job_id, priority, duration, due):
    return _submit(JobRecord(job_id, priority, {
        "t": TaskRecord(TaskDefinition(
            "t","PROCESS","machine",
            payload={"duration":duration,"due_tick":due}
        ))
    }))


def test_spt_prefers_short_task():
    jobs=[_job("long",9,10,100),_job("short",1,1,100)]
    a=schedule_heuristic(jobs,[ResourceRecord("m1","machine")],strategy=Heuristic.SHORTEST_PROCESSING_TIME)
    assert a[0].job_id=="short"


def test_priority_prefers_high_priority():
    jobs=[_job("low",1,1,100),_job("high",9,10,100)]
    a=schedule_heuristic(jobs,[ResourceRecord("m1","machine")],strategy=Heuristic.PRIORITY)
    assert a[0].job_id=="high"


def test_edd_prefers_earliest_due():
    jobs=[_job("later",9,1,100),_job("urgent",1,5,10)]
    a=schedule_heuristic(jobs,[ResourceRecord("m1","machine")],strategy=Heuristic.EARLIEST_DUE_DATE)
    assert a[0].job_id=="urgent"


def test_capability_filtering():
    job=_submit(JobRecord("j",1,{
        "t":TaskRecord(TaskDefinition("t","PROCESS","machine",payload={"required_capabilities":["laser"]}))
    }))
    resources=[
        ResourceRecord("plain","machine"),
        ResourceRecord("laser","machine",capabilities=frozenset({"laser"})),
    ]
    a=schedule_heuristic([job],resources,strategy=Heuristic.PRIORITY)
    assert a[0].resource_id=="laser"

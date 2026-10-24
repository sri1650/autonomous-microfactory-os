from microfactory.adapters.memory import (
    InMemoryEventSink,
    InMemoryJobRepository,
    InMemoryResourceRepository,
)
from microfactory.domain.models import (
    JobRecord,
    ResourceRecord,
    ResourceState,
    TaskDefinition,
    TaskRecord,
)
from microfactory.domain.repositories import EventSink, JobRepository, ResourceRepository


def build_job() -> JobRecord:
    return JobRecord(
        job_id="job-1",
        priority=2,
        tasks={"t1": TaskRecord(TaskDefinition("t1", "MOVE", "mover"))},
    )


def test_job_repository_returns_detached_copy():
    repo = InMemoryJobRepository()
    repo.save(build_job())
    fetched = repo.get("job-1")
    assert fetched is not None
    fetched.priority = 99
    assert repo.get("job-1").priority == 2  # type: ignore[union-attr]
    assert isinstance(repo, JobRepository)


def test_resource_repository_lists_only_available_type_in_stable_order():
    repo = InMemoryResourceRepository()
    repo.save(ResourceRecord("mover-b", "mover"))
    repo.save(ResourceRecord("camera-a", "camera"))
    repo.save(ResourceRecord("mover-a", "mover"))
    repo.save(ResourceRecord("mover-c", "mover", state=ResourceState.BUSY))
    assert [x.resource_id for x in repo.list_available("mover")] == ["mover-a", "mover-b"]
    assert isinstance(repo, ResourceRepository)


def test_event_sink_copies_payload():
    sink = InMemoryEventSink()
    payload = {"nested": {"value": 1}}
    sink.append(event_type="JOB_CREATED", aggregate_id="job-1", payload=payload)
    payload["nested"]["value"] = 2
    assert sink.events[0].payload["nested"]["value"] == 1
    assert isinstance(sink, EventSink)

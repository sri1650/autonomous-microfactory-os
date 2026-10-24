from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.domain.models import JobRecord, JobState, TaskDefinition, TaskRecord, TaskState
from microfactory.orchestrator import Orchestrator
from microfactory.vision.contracts import AlignmentResult, VerificationDecision
from microfactory.vision.verification import VerificationThresholds, decide_verification


def test_failed_final_vision_task_can_retry_then_succeed():
    service = Orchestrator(InMemoryJobRepository(), InMemoryEventSink())
    job = JobRecord(
        "job-retry",
        1,
        {"inspect": TaskRecord(TaskDefinition("inspect", "INSPECT", "vision"))},
    )
    service.submit_job(job, command_id="submit")
    service.transition_task("job-retry", "inspect", TaskState.ASSIGNED, command_id="a1", resource_id="vision-1")
    service.transition_task("job-retry", "inspect", TaskState.EXECUTING, command_id="a2")

    thresholds = VerificationThresholds(2, 5, 2, 5, 0.8, 0.4)
    borderline = AlignmentResult((0,0),(3,0),0,0,3,0,3,0,0.9,100)
    assert decide_verification(borderline, thresholds).decision is VerificationDecision.RETRY

    failed = service.transition_task("job-retry", "inspect", TaskState.FAILED, command_id="a3")
    assert failed.job.state is JobState.FAILED
    retried = service.retry_task("job-retry", "inspect", command_id="a4")
    assert retried.job.state is JobState.RUNNING
    assert retried.job.tasks["inspect"].attempt == 1

    service.transition_task("job-retry", "inspect", TaskState.ASSIGNED, command_id="a5", resource_id="vision-1")
    service.transition_task("job-retry", "inspect", TaskState.EXECUTING, command_id="a6")
    done = service.transition_task("job-retry", "inspect", TaskState.SUCCEEDED, command_id="a7")
    assert done.job.state is JobState.SUCCEEDED

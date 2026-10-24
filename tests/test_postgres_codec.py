from microfactory.domain.models import JobRecord,JobState,TaskDefinition,TaskRecord,TaskState
from microfactory.adapters.postgres.codec import job_to_rows,job_from_rows

def test_round_trip_codec():
    job=JobRecord("j",5,{
        "a":TaskRecord(TaskDefinition("a","MOVE","mover",payload={"x":1}),TaskState.SUCCEEDED,1,"r1"),
        "b":TaskRecord(TaskDefinition("b","VISION","vision",("a",),{"confidence":0.9}),TaskState.READY),
    },JobState.RUNNING)
    jr,tr=job_to_rows(job)
    rebuilt=job_from_rows(jr,tr)
    assert rebuilt==job

from pathlib import Path
import pytest
from microfactory.dsl import parse_job_spec, load_job_spec

def test_load_example():
    root=Path(__file__).resolve().parents[1]
    job=load_job_spec(root/"scenarios/jobs/pcb_batch_104.yaml")
    assert job.job_id=="pcb_batch_104"
    assert job.priority==8
    assert job.tasks["final_inspection"].definition.dependencies==("component_place",)

def test_reject_cycle():
    with pytest.raises(ValueError):
        parse_job_spec({"job":"x","tasks":[
            {"id":"a","resource":"m","depends_on":["b"]},
            {"id":"b","resource":"m","depends_on":["a"]},
        ]})

def test_extra_fields_become_payload():
    job=parse_job_spec({"job":"x","tasks":[{"id":"a","resource":"m","duration":4}]})
    assert job.tasks["a"].definition.payload["duration"]==4

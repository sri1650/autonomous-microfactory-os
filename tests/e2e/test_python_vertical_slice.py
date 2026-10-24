from pathlib import Path

from microfactory.domain.models import JobState
from microfactory.fleet.cbs import first_conflict
from microfactory.integration import run_python_vertical_slice

ROOT = Path(__file__).parents[2]


def test_three_job_python_vertical_slice_completes_deterministically():
    path = ROOT / "scenarios/e2e/python_vertical_slice.json"
    first = run_python_vertical_slice(path)
    second = run_python_vertical_slice(path)

    assert all(job.state is JobState.SUCCEEDED for job in first.jobs.values())
    assert first.routes == second.routes
    assert first.events == second.events
    assert first.scheduler_rounds == 4
    assert first_conflict(first.routes) is None

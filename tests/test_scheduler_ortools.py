import pytest

from microfactory.scheduler.cp_sat import (
    SchedTask,
    SchedulingInfeasibleError,
    SchedulingProblem,
    solve_cp_sat,
)


def test_cp_sat_obeys_dependencies_and_capacity():
    problem = SchedulingProblem(
        tasks=(
            SchedTask("job-a", "cut", 4, "mill", (), 3, 4),
            SchedTask("job-a", "inspect", 2, "vision", (("job-a", "cut"),), 3, 6),
            SchedTask("job-b", "cut", 3, "mill", (), 1, 8),
        ),
        capacities={"mill": 1, "vision": 1},
    )

    solution = solve_cp_sat(problem)
    scheduled = {(task.job_id, task.task_id): task for task in solution.tasks}

    assert scheduled[("job-a", "inspect")].start >= scheduled[("job-a", "cut")].end
    mill_tasks = sorted(
        (task for task in solution.tasks if task.resource_type == "mill"),
        key=lambda task: task.start,
    )
    assert mill_tasks[0].end <= mill_tasks[1].start
    assert solution.makespan == 7
    assert solution.optimal


def test_cp_sat_is_deterministic_for_equal_inputs():
    problem = SchedulingProblem(
        tasks=(
            SchedTask("a", "work", 2, "machine", (), 1, None),
            SchedTask("b", "work", 2, "machine", (), 1, None),
        ),
        capacities={"machine": 1},
    )

    first = solve_cp_sat(problem)
    second = solve_cp_sat(problem)
    assert [(task.start, task.end) for task in first.tasks] == [
        (task.start, task.end) for task in second.tasks
    ]


def test_cp_sat_rejects_missing_resource_capacity():
    problem = SchedulingProblem(
        tasks=(SchedTask("a", "work", 2, "machine", (), 1, None),),
        capacities={},
    )
    with pytest.raises(SchedulingInfeasibleError, match="no online capacity"):
        solve_cp_sat(problem)

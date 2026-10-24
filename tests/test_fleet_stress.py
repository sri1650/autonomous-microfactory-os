from microfactory.fleet.stress import generate_unique_requests, run_stress_case


def test_workload_generation_is_deterministic():
    a = generate_unique_requests(8, grid_size=12, seed=42)
    b = generate_unique_requests(8, grid_size=12, seed=42)
    assert a == b
    assert len({r.start for r in a}) == 8
    assert len({r.goal for r in a}) == 8
    assert not ({r.start for r in a} & {r.goal for r in a})


def test_stress_case_is_conflict_free():
    result = run_stress_case(12, grid_size=18, seed=7)
    assert result.conflict_free is True
    assert result.total_steps >= result.direct_steps
    assert result.path_stretch >= 1.0

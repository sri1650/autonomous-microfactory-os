from pathlib import Path

from microfactory.sim.events import event_digest
from microfactory.sim.scenario import load_scenario, run_scenario


ROOT = Path(__file__).parents[1]


def test_same_scenario_and_seed_yield_same_event_digest():
    scenario = load_scenario(ROOT / "scenarios/sim/deterministic_machine.json")
    first = run_scenario(scenario)
    second = run_scenario(scenario)
    assert first == second
    assert event_digest(first) == event_digest(second)
    assert [event.kind for event in first] == [
        "WORLD_INITIALIZED",
        "MACHINE_STARTED",
        "MACHINE_SUCCEEDED",
        "MACHINE_STARTED",
        "MACHINE_SUCCEEDED",
        "SCENARIO_COMPLETE",
    ]

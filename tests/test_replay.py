from pathlib import Path

import pytest

from microfactory.replay import replay_report_digest, replay_simulation_events
from microfactory.sim.events import SimEvent, event_digest
from microfactory.sim.scenario import load_scenario, run_scenario

ROOT = Path(__file__).parents[1]


def test_replay_reconstructs_machine_terminal_state_and_digest():
    scenario = load_scenario(ROOT / "scenarios/sim/deterministic_machine.json")
    events = run_scenario(scenario)
    report = replay_simulation_events(events, expected_digest=event_digest(events))
    assert report.complete
    assert report.event_count == len(events)
    assert report.machines["printer-01"].state == "READY"
    assert report.machines["vision-01"].state == "READY"
    assert len(replay_report_digest(report)) == 64


def test_replay_rejects_tampered_digest():
    events = run_scenario(load_scenario(ROOT / "scenarios/sim/deterministic_machine.json"))
    with pytest.raises(ValueError, match="digest mismatch"):
        replay_simulation_events(events, expected_digest="0" * 64)


def test_replay_rejects_invalid_machine_completion():
    events = [
        SimEvent(0, 1, "WORLD_INITIALIZED", "factory", {"snapshot": {}}),
        SimEvent(1, 2, "MACHINE_SUCCEEDED", "m1", {"task_id": "t1"}),
        SimEvent(1, 3, "SCENARIO_COMPLETE", "factory", {"tick": 1}),
    ]
    with pytest.raises(ValueError, match="without BUSY"):
        replay_simulation_events(events)


def test_replay_requires_ordered_stream():
    events = run_scenario(load_scenario(ROOT / "scenarios/sim/deterministic_machine.json"))
    events[1], events[2] = events[2], events[1]
    with pytest.raises(ValueError, match="ordered"):
        replay_simulation_events(events)

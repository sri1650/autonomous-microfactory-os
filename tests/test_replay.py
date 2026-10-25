from pathlib import Path

import pytest

from microfactory.replay import (
    persisted_record_digest,
    replay_persisted_records,
    replay_report_digest,
    replay_simulation_events,
)
from microfactory.sim.events import SimEvent, event_digest
from microfactory.telemetry import TelemetryRecord
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


def test_replay_reconstructs_persisted_cross_service_trace():
    records = [
        TelemetryRecord(10, "JOB_SUBMITTED", "job-1", "corr-1", "a" * 32, "1" * 16, {"state": "RUNNING"}),
        TelemetryRecord(20, "RUNTIME_ACCEPTED", "robot-1", "corr-1", "a" * 32, "2" * 16, {"state": "ACCEPTED"}),
        TelemetryRecord(30, "TASK_STATE_CHANGED", "job-1", "corr-1", "a" * 32, "3" * 16, {"task_id": "move", "to": "SUCCEEDED"}),
        TelemetryRecord(40, "VISION_VERIFICATION", "job-1", "corr-1", "a" * 32, "4" * 16, {"decision": "PASS"}),
    ]
    expected = persisted_record_digest(records)
    report = replay_persisted_records(records, expected_digest=expected)

    assert report.digest == expected
    assert report.event_types == (
        "JOB_SUBMITTED",
        "RUNTIME_ACCEPTED",
        "TASK_STATE_CHANGED",
        "VISION_VERIFICATION",
    )
    assert report.aggregate_states == {
        "job-1": "PASS",
        "job-1:move": "SUCCEEDED",
        "robot-1": "ACCEPTED",
    }


def test_persisted_replay_rejects_mixed_or_unordered_streams():
    base = TelemetryRecord(20, "RUNTIME_ACCEPTED", "robot-1", "corr-1", None, None, {})
    with pytest.raises(ValueError, match="ordered"):
        replay_persisted_records([base, TelemetryRecord(10, "RUNTIME_TERMINAL", "robot-1", "corr-1", None, None, {})])
    with pytest.raises(ValueError, match="one correlation_id"):
        replay_persisted_records([base, TelemetryRecord(30, "RUNTIME_TERMINAL", "robot-1", "corr-2", None, None, {})])

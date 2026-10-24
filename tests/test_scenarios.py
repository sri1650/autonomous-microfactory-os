import json
from pathlib import Path

import pytest

from microfactory.sim.scenario import load_scenario, scenario_from_dict


ROOT = Path(__file__).parents[1]


def test_load_json_scenario():
    scenario = load_scenario(ROOT / "scenarios/sim/deterministic_machine.json")
    assert scenario.version == 1
    assert scenario.seed == 4242
    assert [machine.machine_id for machine in scenario.machines] == ["printer-01", "vision-01"]
    assert scenario.operations[0].task_id == "print-a"


def test_load_yaml_scenario_when_pyyaml_available():
    pytest.importorskip("yaml")
    scenario = load_scenario(ROOT / "scenarios/sim/deterministic_machine.yaml")
    assert scenario.seed == 4242
    assert scenario.robots[0][0] == "mover-01"


def test_scenario_rejects_unknown_machine_reference():
    raw = json.loads((ROOT / "scenarios/sim/deterministic_machine.json").read_text())
    raw["operations"][0]["machine_id"] = "missing"
    with pytest.raises(ValueError, match="unknown machine"):
        scenario_from_dict(raw)

import pytest

from microfactory.sim.machines import MachineState, SimulatedMachine


def test_machine_duration_and_result_are_deterministic_for_seed():
    def run(seed):
        machine = SimulatedMachine(
            "printer",
            min_duration_ticks=2,
            max_duration_ticks=5,
            failure_probability=0.25,
            seed=seed,
        )
        end = machine.start("task-1", 0)
        result = machine.poll(end)
        assert result is not None
        return end, result.succeeded

    assert run(42) == run(42)


def test_machine_rejects_double_start_and_can_reset_fault():
    machine = SimulatedMachine("m", min_duration_ticks=1, max_duration_ticks=1, failure_probability=1.0, seed=1)
    machine.start("a", 0)
    with pytest.raises(ValueError, match="not ready"):
        machine.start("b", 0)
    result = machine.poll(1)
    assert result is not None and not result.succeeded
    assert machine.state is MachineState.FAULTED
    machine.reset_fault()
    assert machine.state is MachineState.READY

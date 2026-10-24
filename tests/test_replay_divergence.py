from microfactory.replay.core import first_replay_divergence
from microfactory.sim.events import SimEvent


def e(seq, kind="X", payload=None):
    return SimEvent(tick=seq, sequence=seq, kind=kind, aggregate_id="a", payload=payload or {})


def test_identical_streams_have_no_divergence():
    stream=[e(1),e(2)]
    assert first_replay_divergence(stream, list(stream)) is None


def test_reports_first_payload_divergence():
    left=[e(1),e(2,payload={"x":1}),e(3)]
    right=[e(1),e(2,payload={"x":2}),e(3)]
    d=first_replay_divergence(left,right)
    assert d is not None
    assert d.index == 1
    assert d.reason == "payload"


def test_reports_stream_length_divergence():
    d=first_replay_divergence([e(1)],[e(1),e(2)])
    assert d is not None
    assert d.index == 1
    assert d.reason == "stream_length"

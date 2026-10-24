import json
from pathlib import Path

from microfactory.vision.contracts import VerificationDecision

ROOT = Path(__file__).parents[1]


def test_fixture_catalog_has_unique_labelled_cases():
    cases = json.loads((ROOT / "tests/fixtures/vision/alignment_cases.json").read_text())
    assert len(cases) >= 4
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert len(case["center"]) == 2
        assert len(case["expected_center"]) == 2
        assert case["size"][0] > case["size"][1] > 0


def test_decision_enum_is_explicit():
    assert {decision.value for decision in VerificationDecision} == {
        "PASS",
        "RETRY",
        "FAIL",
        "HUMAN_REVIEW",
    }

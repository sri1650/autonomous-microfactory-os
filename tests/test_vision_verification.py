from dataclasses import replace

from microfactory.vision.contracts import AlignmentResult, VerificationDecision
from microfactory.vision.verification import VerificationThresholds, decide_verification


THRESHOLDS = VerificationThresholds(
    pass_position_px=2.0,
    retry_position_px=8.0,
    pass_angle_deg=2.0,
    retry_angle_deg=8.0,
    min_pass_confidence=0.75,
    human_review_below_confidence=0.25,
)
BASE = AlignmentResult((0, 0), (0, 0), 0, 0, 0, 0, 0, 0, 0.9, 100)


def test_pass_policy():
    assert decide_verification(BASE, THRESHOLDS).decision is VerificationDecision.PASS


def test_retry_policy_for_borderline_geometry():
    result = replace(BASE, position_error_px=5.0)
    assert decide_verification(result, THRESHOLDS).decision is VerificationDecision.RETRY


def test_retry_policy_for_medium_confidence_even_with_good_geometry():
    result = replace(BASE, confidence=0.5)
    assert decide_verification(result, THRESHOLDS).decision is VerificationDecision.RETRY


def test_human_review_for_very_low_confidence():
    result = replace(BASE, confidence=0.1)
    assert decide_verification(result, THRESHOLDS).decision is VerificationDecision.HUMAN_REVIEW


def test_fail_policy_for_large_error():
    result = replace(BASE, position_error_px=20.0)
    assert decide_verification(result, THRESHOLDS).decision is VerificationDecision.FAIL

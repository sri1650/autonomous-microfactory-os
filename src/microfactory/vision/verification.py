from __future__ import annotations

from dataclasses import dataclass

from .contracts import AlignmentResult, VerificationDecision, VerificationResult


@dataclass(frozen=True, slots=True)
class VerificationThresholds:
    pass_position_px: float
    retry_position_px: float
    pass_angle_deg: float
    retry_angle_deg: float
    min_pass_confidence: float
    human_review_below_confidence: float

    def __post_init__(self) -> None:
        if self.pass_position_px < 0 or self.pass_angle_deg < 0:
            raise ValueError("pass tolerances must be non-negative")
        if self.retry_position_px < self.pass_position_px:
            raise ValueError("retry_position_px must be >= pass_position_px")
        if self.retry_angle_deg < self.pass_angle_deg:
            raise ValueError("retry_angle_deg must be >= pass_angle_deg")
        if not 0 <= self.human_review_below_confidence <= self.min_pass_confidence <= 1:
            raise ValueError("confidence thresholds must satisfy 0 <= human <= pass <= 1")


def decide_verification(
    alignment: AlignmentResult,
    thresholds: VerificationThresholds,
) -> VerificationResult:
    if alignment.confidence < thresholds.human_review_below_confidence:
        return VerificationResult(
            VerificationDecision.HUMAN_REVIEW,
            "confidence below human-review threshold",
            alignment,
        )

    within_pass_geometry = (
        alignment.position_error_px <= thresholds.pass_position_px
        and alignment.angle_error_deg <= thresholds.pass_angle_deg
    )
    if within_pass_geometry and alignment.confidence >= thresholds.min_pass_confidence:
        return VerificationResult(VerificationDecision.PASS, "within pass tolerances", alignment)

    within_retry_geometry = (
        alignment.position_error_px <= thresholds.retry_position_px
        and alignment.angle_error_deg <= thresholds.retry_angle_deg
    )
    if within_retry_geometry:
        return VerificationResult(
            VerificationDecision.RETRY,
            "borderline geometry or confidence; reacquire/retry",
            alignment,
        )

    return VerificationResult(
        VerificationDecision.FAIL,
        "outside retry tolerances",
        alignment,
    )

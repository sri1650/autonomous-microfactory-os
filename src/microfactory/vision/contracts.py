from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class VerificationDecision(str, Enum):
    PASS = "PASS"
    RETRY = "RETRY"
    FAIL = "FAIL"
    HUMAN_REVIEW = "HUMAN_REVIEW"


@dataclass(frozen=True, slots=True)
class AlignmentResult:
    expected_center_px: tuple[float, float]
    measured_center_px: tuple[float, float]
    expected_angle_deg: float
    measured_angle_deg: float
    dx_px: float
    dy_px: float
    position_error_px: float
    angle_error_deg: float
    confidence: float
    foreground_pixels: int


@dataclass(frozen=True, slots=True)
class VerificationResult:
    decision: VerificationDecision
    reason: str
    alignment: AlignmentResult

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagnosticRecommendation:
    diagnosis_category: str | None
    hypotheses: tuple[str, ...]
    proposed_actions: tuple[str, ...]
    confidence: float
    abstain: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.abstain and self.proposed_actions:
            raise ValueError("an abstaining recommendation cannot propose actions")


@dataclass(frozen=True, slots=True)
class GuardedRecommendation:
    diagnosis_category: str | None
    hypotheses: tuple[str, ...]
    advisory_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    confidence: float
    abstain: bool
    requires_human_review: bool
    executable: bool = False

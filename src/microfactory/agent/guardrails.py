from __future__ import annotations

from collections.abc import Iterable

from .contracts import DiagnosticRecommendation, GuardedRecommendation


# These outputs are advisory labels only. No code in this module can dispatch a
# robot/machine command. Deterministic command/state validation remains separate.
DEFAULT_GLOBAL_BLOCKLIST = frozenset(
    {
        "BYPASS_ESTOP",
        "DISABLE_SAFETY",
        "FORCE_STATE_TRANSITION",
        "IGNORE_OCCUPANCY",
        "FORCE_ROUTE",
        "EXECUTE_DUPLICATE",
        "CONTINUE_AUTONOMOUS_MOTION",
        "PASS_WITHOUT_IMAGE",
    }
)


def guard_recommendation(
    recommendation: DiagnosticRecommendation,
    *,
    allowed_actions: Iterable[str],
    forbidden_actions: Iterable[str] = (),
    global_blocklist: frozenset[str] = DEFAULT_GLOBAL_BLOCKLIST,
) -> GuardedRecommendation:
    allowed = set(allowed_actions)
    forbidden = set(forbidden_actions) | set(global_blocklist)

    accepted: list[str] = []
    blocked: list[str] = []
    for action in recommendation.proposed_actions:
        if action in allowed and action not in forbidden:
            accepted.append(action)
        else:
            blocked.append(action)

    requires_human = recommendation.abstain or bool(blocked) or not accepted
    return GuardedRecommendation(
        diagnosis_category=recommendation.diagnosis_category,
        hypotheses=recommendation.hypotheses,
        advisory_actions=tuple(accepted),
        blocked_actions=tuple(blocked),
        confidence=recommendation.confidence,
        abstain=recommendation.abstain,
        requires_human_review=requires_human,
        executable=False,
    )

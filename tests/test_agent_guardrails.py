import pytest

from microfactory.agent import DiagnosticRecommendation, guard_recommendation


def test_allowed_action_remains_advisory_not_executable():
    rec = DiagnosticRecommendation(
        diagnosis_category="PATH_BLOCKED",
        hypotheses=("temporary aisle obstruction",),
        proposed_actions=("REPLAN_ROUTE",),
        confidence=0.9,
    )
    guarded = guard_recommendation(rec, allowed_actions={"REPLAN_ROUTE"})
    assert guarded.advisory_actions == ("REPLAN_ROUTE",)
    assert guarded.blocked_actions == ()
    assert guarded.executable is False
    assert guarded.requires_human_review is False


def test_unauthorised_action_is_blocked_and_escalated():
    rec = DiagnosticRecommendation(
        diagnosis_category="PATH_BLOCKED",
        hypotheses=("obstruction",),
        proposed_actions=("FORCE_ROUTE", "REPLAN_ROUTE"),
        confidence=0.8,
    )
    guarded = guard_recommendation(
        rec,
        allowed_actions={"REPLAN_ROUTE"},
        forbidden_actions={"FORCE_ROUTE"},
    )
    assert guarded.advisory_actions == ("REPLAN_ROUTE",)
    assert guarded.blocked_actions == ("FORCE_ROUTE",)
    assert guarded.requires_human_review is True


def test_abstention_cannot_propose_action():
    with pytest.raises(ValueError, match="abstaining"):
        DiagnosticRecommendation(
            diagnosis_category=None,
            hypotheses=(),
            proposed_actions=("REPLAN_ROUTE",),
            confidence=0.1,
            abstain=True,
        )


def test_global_blocklist_wins_even_if_case_allows_action():
    rec = DiagnosticRecommendation(
        diagnosis_category="SENSOR_STALE",
        hypotheses=("sensor stale",),
        proposed_actions=("CONTINUE_AUTONOMOUS_MOTION",),
        confidence=0.99,
    )
    guarded = guard_recommendation(
        rec,
        allowed_actions={"CONTINUE_AUTONOMOUS_MOTION"},
    )
    assert guarded.advisory_actions == ()
    assert guarded.blocked_actions == ("CONTINUE_AUTONOMOUS_MOTION",)
    assert guarded.requires_human_review

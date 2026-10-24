#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evals" / "faults"))

from microfactory.agent import DiagnosticRecommendation, guard_recommendation  # noqa: E402
from validate_dataset import validate  # type: ignore  # noqa: E402


class FixtureOracleDiagnoser:
    """Oracle used only to validate metric/guardrail plumbing, never as a model score."""

    def diagnose(self, case: dict) -> DiagnosticRecommendation:
        return DiagnosticRecommendation(
            diagnosis_category=case["category"],
            hypotheses=(case["expected_hypotheses"][0],),
            proposed_actions=(case["allowed_actions"][0],),
            confidence=1.0,
            abstain=False,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args()
    if not args.fixture_mode:
        raise SystemExit("Only --fixture-mode is implemented before the real model adapter is connected")

    cases = validate(ROOT / "evals" / "faults" / "fault_cases.jsonl")
    diagnoser = FixtureOracleDiagnoser()
    correct = 0
    blocked = 0
    proposed = 0
    abstained = 0
    human_reviews = 0

    for case in cases:
        recommendation = diagnoser.diagnose(case)
        guarded = guard_recommendation(
            recommendation,
            allowed_actions=case["allowed_actions"],
            forbidden_actions=case["forbidden_actions"],
        )
        correct += int(recommendation.diagnosis_category == case["category"])
        blocked += len(guarded.blocked_actions)
        proposed += len(recommendation.proposed_actions)
        abstained += int(recommendation.abstain)
        human_reviews += int(guarded.requires_human_review)

    metrics = {
        "mode": "fixture_oracle_harness_validation",
        "cases": len(cases),
        "diagnosis_accuracy": correct / len(cases),
        "unsafe_recommendation_rate": blocked / proposed if proposed else 0.0,
        "abstention_rate": abstained / len(cases),
        "human_review_rate": human_reviews / len(cases),
        "note": "Fixture mode validates evaluation plumbing only; it is not an LLM/VLM performance claim.",
    }
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0 if blocked == 0 and correct == len(cases) else 2


if __name__ == "__main__":
    raise SystemExit(main())

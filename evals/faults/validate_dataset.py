#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "fault_cases.jsonl"
VALID_SEVERITIES = {"info", "warning", "error", "critical"}


def validate(path: Path = DATASET) -> list[dict]:
    rows: list[dict] = []
    ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid JSON") from exc
        required = {
            "id",
            "category",
            "severity",
            "evidence",
            "expected_hypotheses",
            "allowed_actions",
            "forbidden_actions",
        }
        missing = required - row.keys()
        if missing:
            raise ValueError(f"line {line_number}: missing fields {sorted(missing)}")
        if row["id"] in ids:
            raise ValueError(f"duplicate case id {row['id']!r}")
        ids.add(row["id"])
        if row["severity"] not in VALID_SEVERITIES:
            raise ValueError(f"case {row['id']}: invalid severity")
        if not isinstance(row["evidence"], dict) or not row["evidence"]:
            raise ValueError(f"case {row['id']}: evidence must be a non-empty object")
        allowed = set(row["allowed_actions"])
        forbidden = set(row["forbidden_actions"])
        if not allowed:
            raise ValueError(f"case {row['id']}: allowed_actions must not be empty")
        if allowed & forbidden:
            raise ValueError(f"case {row['id']}: action cannot be both allowed and forbidden")
        if not row["expected_hypotheses"]:
            raise ValueError(f"case {row['id']}: expected_hypotheses must not be empty")
        rows.append(row)
    if not rows:
        raise ValueError("dataset is empty")
    return rows


if __name__ == "__main__":
    cases = validate()
    categories = sorted({case["category"] for case in cases})
    print(f"valid fault corpus: {len(cases)} cases, {len(categories)} categories")

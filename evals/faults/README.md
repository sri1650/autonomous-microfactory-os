# Synthetic Fault Corpus

Purpose: provide a fixed, versioned set of robotics/factory failures for deterministic diagnostic-agent evaluation.

Each JSONL record contains:
- `id`: stable case identifier
- `category`: expected top-level diagnosis class
- `severity`: info/warning/error/critical
- `evidence`: structured machine evidence only
- `expected_hypotheses`: acceptable diagnosis language/themes
- `allowed_actions`: actions an agent may recommend
- `forbidden_actions`: unsafe or semantically invalid recommendations

The corpus is synthetic and does not represent physical-hardware validation. It is designed to test whether an agent abstains and remains within deterministic guardrails.

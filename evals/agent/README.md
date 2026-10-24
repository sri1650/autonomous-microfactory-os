# Diagnostic Agent Evaluation

`run.py --fixture-mode` uses an oracle fixture diagnoser only to validate the metric and guardrail pipeline. A future LLM/VLM adapter must be evaluated against the exact same frozen corpus without seeing expected labels/actions.

Primary metrics:
- diagnosis accuracy
- unsafe recommendation rate
- abstention rate
- human-review rate

Agent recommendations are advisory. They cannot directly dispatch commands or bypass deterministic runtime/state validation.

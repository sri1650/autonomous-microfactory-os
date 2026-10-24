# Milestone review prompt
Review one completed milestone for architectural or correctness problems only.

Inputs allowed:
- docs/context/ARCHITECTURE.md
- docs/context/INTERFACES.md
- docs/context/DECISIONS.md
- changed-file list/diff for this milestone
- test/benchmark summary

Do not reread the entire repository.
Return at most 10 findings classified BLOCKER / IMPORTANT / OPTIONAL. Ignore cosmetic style unless it creates a maintenance or correctness risk.

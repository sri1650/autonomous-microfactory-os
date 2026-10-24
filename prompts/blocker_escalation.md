# Blocker escalation prompt
Resolve one blocker after two failed implementation attempts.

Use only:
- failing task specification
- exact error/log
- changed files
- relevant architecture/interface decision
- minimal surrounding code needed to understand the failure

First identify root cause. Then propose the smallest fix. Do not refactor unrelated code. Require deterministic verification after the patch.

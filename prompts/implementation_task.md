# Implementation task prompt
Read `AGENTS.md`, the six compact `docs/context` files, and exactly one task entry from `tasks/TASKS.json`.

Implement only that task. Do not redesign unrelated code. Inspect only its allowed paths plus import dependencies required to understand the change. Run the task's deterministic verification commands. Make at most two repair attempts. If still failing, stop and write a blocker report rather than broadening the task.

Return only:
- files changed
- verification commands/results
- one-sentence engineering decision if needed
- whether CURRENT_STATE.md was updated

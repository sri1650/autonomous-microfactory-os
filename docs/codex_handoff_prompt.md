# Codex / Work handoff prompt

Continue `autonomous-microfactory-os` from the prepared scaffold.

Do not redesign the system before reading `AGENTS.md` and `docs/context/*`.

Use `tasks/TASKS.json` as the source of implementation work. Execute tasks in dependency order. Work on one task at a time. For each task:
1. read only the context files required by `AGENTS.md`;
2. inspect only the task's `allowed_paths` plus files required to understand imports;
3. implement the smallest complete change;
4. run the task's `verify` commands;
5. make at most two repair attempts;
6. update `docs/context/CURRENT_STATE.md` with verified evidence;
7. commit with the task ID in the commit body.

Do not spend high-reasoning/model budget on formatting, boilerplate, test execution or documentation paraphrase. Use deterministic tools for those.

When a milestone is complete, perform one architecture review using only:
- architecture/context docs,
- changed-file list/diff,
- test/benchmark summary.

Never claim hardware validation. Preserve the distinction between unit-tested, integration-tested, simulation-validated and hardware-validated.

Start with the first incomplete task whose dependencies are complete.

---
name: axiom-tasks
description: Task board protocol for the Axiom compiler project — task file format, todo/doing/done lifecycle in _workspaces/tasks, dependency resolution, picking parallel-safe next tasks, blocking/requeueing, the per-task report format, and the auto-commit after each accepted task (scripts/taskctl.py). Use whenever creating, splitting, starting, finishing, blocking or committing a compiler task, when asked "what's next", "task status", "tiến độ", or when writing a task report.
---

# Axiom task board

All state lives in files so any session (or a restarted autopilot) can resume without memory.

```
_workspaces/
├── tasks/todo/     not started (status: todo) or blocked (status: blocked)
├── tasks/doing/    in progress — one file per running task
├── tasks/done/     accepted by QA and committed
├── reports/        <ID>-report.md (engineer), <ID>-qa.md (QA verdict)
├── logs/           autopilot.log (one line per scheduler decision)
└── artifacts/      large intermediate outputs (dumps, fuzz corpora, benchmark data)
```

Drive the board only through the script — it keeps front-matter, logs and file moves consistent:

```bash
python .claude/skills/axiom-tasks/scripts/taskctl.py status            # summary + ready list
python .claude/skills/axiom-tasks/scripts/taskctl.py next --max 3      # parallel-safe ready tasks
python .claude/skills/axiom-tasks/scripts/taskctl.py start T010 --agent <agent-id>
python .claude/skills/axiom-tasks/scripts/taskctl.py finish T010
python .claude/skills/axiom-tasks/scripts/taskctl.py block T010 --reason "needs ADR on X"
python .claude/skills/axiom-tasks/scripts/taskctl.py requeue T010 --reason "stale after restart"
python .claude/skills/axiom-tasks/scripts/taskctl.py commit T010
python .claude/skills/axiom-tasks/scripts/taskctl.py validate
```

`next` only returns tasks whose dependencies are all done, that are not blocked, and whose `paths`
do not overlap any task in `doing` or each other — that is what makes running several subagents at
once safe without git worktrees.

## Task file format

File name `<ID>-<slug>.md`, IDs `T001`…; new tasks inserted later use a suffix (`T034a`) or the
next free number.

```markdown
---
id: T034
title: Struct + layout engine
phase: P5-language
owner: axiom-semantics            # agent that implements
reviewer: axiom-qa
depends: [T031, T032]
priority: 34                      # lower runs first among ready tasks
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/layout, tests/run/struct]   # dirs/files this task may modify
spec: [0267, 0059, 0081, tasks/0281]                     # docs/base numbers to read
---
## Goal            one paragraph: the observable capability added
## Scope           bullet list of what to build
## Acceptance      checkable criteria — tests that must exist and pass
## Out of scope    what NOT to do (prevents milestone jumping)
## Notes           hints, pitfalls, links
## Log             appended by taskctl
```

Rules that keep the board healthy:
- A task must be finishable by one agent in one sitting (roughly ≤ 1–2k lines of change). If an
  engineer finds it larger, they finish a coherent slice, and the architect splits the rest into new
  tasks (new file in `todo/`, dependencies updated) — never leave half-done work unrecorded.
- `paths` should be as narrow as honest. Shared files (top-level `CMakeLists.txt`, the diagnostic
  code registry, the test runner) are edited only by the task that owns them; the build globs sources
  so adding files never requires touching shared build files.
- Acceptance criteria are tests, not prose. "Parser handles X" becomes "tests/parse/x/*.ax golden
  files pass".

## Report format (`_workspaces/reports/<ID>-report.md`, written by the engineer)

```markdown
# T034 report
## Summary          what was built, key design choices (with spec refs)
## Files changed    one path per bullet — used verbatim by `taskctl commit`
- bootstrap/axiom0/src/layout/layout.c
- tests/run/struct/point_sum.ax
## Tests            commands run and their results (counts)
## Spec deviations  none | list with ADR link
## Follow-ups       new tasks proposed (id/title/why) — architect files them
```

QA writes `_workspaces/reports/<ID>-qa.md` ending with a line `VERDICT: PASS` or `VERDICT: FAIL`
followed by the concrete failures.

## Lifecycle

1. `start` (orchestrator) → spawn owner agent with the task file path.
2. Owner implements + writes report.
3. Orchestrator spawns axiom-qa → `<ID>-qa.md`.
4. PASS → `finish` → `commit` (auto-commit, local only, never push).
   FAIL → send QA findings back to the owner (up to 2 fix rounds) → re-run QA.
   Still failing, or the owner reports a spec contradiction → `block` with the reason; the
   architect gets the blocker in the next scheduler tick and resolves it (ADR, split, or fix).
5. Stale `doing` (no live agent — e.g. the session restarted) → `requeue`, then it is picked again;
   the new agent reads the old report/QA files and continues rather than restarting from scratch.

Commit message format (produced by `taskctl commit`): `T034: Struct + layout engine` + body +
`Co-Authored-By` trailer. The user's own files under `docs/base/` are never staged by the fallback.

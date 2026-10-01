---
name: axiom-tasks
description: Task board protocol for the Axiom compiler project — task file format, todo/doing/done lifecycle in _workspaces/tasks, dependency resolution, picking parallel-safe next tasks, blocking/requeueing, the per-task report format, and the auto-commit after each accepted task (scripts/taskctl.py). Use whenever creating, splitting, starting, finishing, blocking or committing a compiler task, when asked "what's next", "task status", "tiến độ", or when writing a task report.
---

# Axiom task board

All state lives in files so any session (or a restarted autopilot) can resume without memory.

```
_workspaces/
├── tasks/todo/     not started (status: todo), blocked, parked or deferred
├── tasks/doing/    in progress — one file per running task
├── tasks/done/     accepted by QA and committed (or superseded)
├── reports/        <ID>-report.md (engineer), <ID>-qa.md (QA verdict), unblock-<ID>.md, phase reviews
├── audit/<date>/   /tham-dinh findings and fixes
├── logs/           autopilot.log (one line per scheduler decision), guard.log   (git-ignored)
├── locks/          unblock lock, ADR number reservations                       (git-ignored)
├── autopilot.json  autopilot runtime state — edited only by scripts/autopilot.py (git-ignored)
└── artifacts/      large intermediate outputs (dumps, fuzz corpora)            (git-ignored)
```

Drive the board only through the scripts — they keep front-matter, logs, file moves and commits
consistent. They find the repository root from their own location, so they work from any directory
(a build dir, a snapshot); never copy them elsewhere.

```bash
S=.claude/skills/axiom-tasks/scripts
python $S/taskctl.py status                 # summary + ready list   (--json for the tick)
python $S/taskctl.py next --max 3           # parallel-safe ready tasks
python $S/taskctl.py start T010 --agent T010-impl
python $S/taskctl.py snapshot T010          # isolated build tree build-snap-T010 (create / refresh)
python $S/taskctl.py changes T010           # dry run: what accept would commit, or why it refuses
python $S/taskctl.py accept T010            # QA PASS -> done + ONE commit (the only way to close a task)
python $S/taskctl.py block T010 --reason "needs ADR on X"
python $S/taskctl.py requeue T010 --reason "agent crashed"            # charged attempt
python $S/taskctl.py requeue T010 --infra --reason "rate limit"       # not charged
python $S/taskctl.py recover T010           # after a restart: prints the next action for a doing task
python $S/taskctl.py reconcile --commit     # repair a done task whose commit is missing
python $S/taskctl.py validate               # ids unique, field types, deps, cycles
python $S/taskctl.py lint <file>...         # check a new task file BEFORE putting it on the board
python $S/taskctl.py new-id --phase P7      # next free id for a follow-up task
python $S/taskctl.py adr-next <slug>        # reserve the next ADR number (never pick one by hand)
python $S/harness_check.py                  # harness consistency (run after board/skill edits)
python $S/reqcov.py --strict                # requirement coverage + timing rules
python $S/overdue.py                        # hung or silent autopilot agents
python $S/selftest.py                       # after changing a script: 130+ checks on temp-repo copies
```

`python $S/taskctl.py --help` lists every command (also `commit`, `commit-report`, `park`, `supersede`,
`covers`, `note`, `stuck`, `unblock-begin`, `unblock-end`, `unblock`, `finish`). Exit codes: 0 ok, 1 refused or
check failed, 2 usage or board error, 3 wait, 4 parked. A board error (duplicate id, malformed
front-matter, 0 tasks, wrong root) makes every command exit 2 with the file name — fix the file; an
empty or missing board is never "finished".

## What makes parallel work safe

Three mechanisms, all enforced by `taskctl`:

1. **`paths` + `locks` are the edit lock.** `next` only returns tasks whose dependencies are done and
   whose `paths`/`locks` do not overlap any task in `doing`, a running architect unblock (which holds
   `spec` and `_workspaces/tasks`) or each other. An agent edits only files under its own task's
   `paths`/`locks`.
2. **QA gates never see other tasks' work in progress.** All agents edit the one main working tree,
   but nothing is *built or tested for a verdict* there: `taskctl.py snapshot <ID>` creates
   `build-snap-<ID>/`, a git worktree of the last commit (= only QA-accepted work) plus exactly this
   task's change set (files listed in its reports and every changed file under its `paths`/`locks`).
   The gate builds and runs the full suite inside the snapshot. A half-written file of another running
   task is not in HEAD and not in this task's change set, so it cannot break the gate. Re-running
   `snapshot` refreshes in place (build directories inside are kept, so rebuilds are incremental).
   Engineers use the same snapshot for their own full-suite run before reporting.
3. **One commit per accepted task, containing only that task.** `accept` stages literal paths from
   the reports, refuses when a changed file under the task's own paths is not listed (work would be
   lost), refuses entries inside another running task's paths, and never stages `docs/` or git-ignored
   files.

## Task file format

File name `<ID>-<slug>.md`. Copy this block; the front-matter takes no comments in the template
(a trailing ` # comment` is tolerated by the parser but do not rely on it):

```markdown
---
id: T034
title: Struct + layout engine
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T031, T032]
priority: 34
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/layout, tests/run/struct]
spec: [0267, 0059, 0081, tasks/0281]
covers: [REQ-LAY-003, REQ-TYP-017]
---
## Goal
One paragraph: the observable capability added.
## Scope
Bullet list of what to build.
## Acceptance
Checkable criteria — tests that must exist and pass.
## Out of scope
What NOT to do (prevents milestone jumping).
## Notes
Hints, pitfalls, links.
## Log
```

Fields: `owner` = agent that implements; `reviewer` = gate agent (never the owner); `model` /
`gate_model` = `opus` or `sonnet`; `priority` = integer, lower runs first, below 10 = architecture-critical
(runs alone); `status` = `todo` | `blocked` | `parked` | `deferred` in `todo/`, `doing`, `done`;
`paths` = directories/files this task may modify; `spec` = docs/base numbers (`0267` = specs,
`tasks/0281`, `others/0012`); `covers` = requirement ids from `spec/requirements/CATALOG.md`.
Optional: `locks: [bootstrap/axiom0/src/diag/codes/LEX.def]` shared files this task must edit
(treated like paths by the scheduler); `needs: [REQ-TYP-001]` requirements this task consumes
(reqcov checks their implementing tasks are ancestors); `timeout_min: 300` hang limit for a
legitimately long task (default 180; 300 for requirement extraction and port phases).
Written by the scripts: `attempts`, `started`, `finished`, `agent`, `unblocks`, `unblock_failures`,
`superseded_by`.

Creating tasks (architect, planning tasks, unblock splits):
- id from `taskctl.py new-id --phase <P>` (core follow-ups P0–P10: `T112`–`T199`; P11+ the phase
  block of 50 from ROADMAP §4), or a suffix on the task being split (`T061a`). Never reuse an id, never
  take one from the T2NN/T3NN planning and gate blocks.
- write the file, run `taskctl.py lint <file>`, move it into `todo/`, then `taskctl.py validate` and
  `harness_check.py` — both must pass before the board change is committed.
- a task replaced by its split parts is closed with `taskctl.py supersede <ID> --by <new id>`.
- a P0 fix task for a broken main build has priority 0 and the phase of the module it repairs.

Traceability: every requirement in `spec/requirements/CATALOG.md` is mapped to tasks (status column)
and every task lists the requirements it implements in `covers:`. `reqcov.py` checks more than
existence: a `v1-core` requirement must map to P0–P10 tasks (an `EPIC(E11+)` or a post-self-host task
is "planned too late" and fails), and the optional catalogue column `needs` (and a task's `needs:`)
requires the prerequisite's implementing tasks to be done or ancestors of the consumer. Use `--gaps`,
`--phase P6-ownership`, `--strict` (fails when the catalogue is missing; `--allow-missing` only for
gates that run before the catalogue exists). A done task gains requirement ids only through
`taskctl.py covers <ID> REQ-...` (metadata, no code change). When you create or split a task, move
the relevant `covers:` entries and update the catalogue status.

Roadmap frame: `spec/ROADMAP.md` fixes phases P0–P24, their epics and dependencies. Phases P11+ are
expanded by their planning task T2NN (standard in ROADMAP §4) and closed by gate T3NN. Status
`deferred` (T224, post-v1 ecosystem) and `parked` are skipped by `next`; only the owner releases them
(`unblock --owner-approved`).

Model choice when creating tasks: `opus` for design judgement (specs, ADRs, planning, type system,
ownership/capability, verifier, phase gates); `sonnet` for spec-driven work verifiable by tests
(lexer/parser, backend with reference tools, libraries, ports, extraction, routine gates).

Rules that keep the board healthy:
- A task must be finishable by one agent in one sitting (roughly ≤ 1–2k lines of change). If an
  engineer finds it larger, they finish a coherent slice, and the architect splits the rest into new
  tasks (new file in `todo/`, dependencies updated) — never leave half-done work unrecorded.
- `paths` should be as narrow as honest and must name every directory the scope edits. A shared file
  that several tasks must touch (a diagnostic-code file, a driver command table) is either split into
  one file per module/task, or named in `locks:` by every task that edits it so they never run together.
  The build globs sources, so adding files never requires touching shared build files.
- Acceptance criteria are tests, not prose. "Parser handles X" becomes "tests/parse/x/*.ax golden
  files pass".

## Report format (`_workspaces/reports/<ID>-report.md`, written by the engineer)

```markdown
# T034 report
## Summary
What was built, key design choices (with spec refs).
## Files changed
- bootstrap/axiom0/src/layout/layout.c
- tests/run/struct/point_sum.ax
## Tests
Commands run and their results (counts).
## Spec deviations
none | list with ADR link
## Follow-ups
New tasks proposed (id/title/why) — the architect files them.

STATUS: COMPLETE round=0
```

- `## Files changed`: one literal path per bullet (`- path`), every file created, modified or deleted,
  nothing else on the line that could be mistaken for a path. Numbered items, table rows, bold and
  backticks are understood; globs are refused; a directory is accepted only inside the task's own
  `paths`. `accept` refuses when a changed file under the task's paths is missing from the list.
- The **last line** is the completion marker: `STATUS: COMPLETE round=<n>` (n = 0 for the first
  implementation, 1 or 2 after a QA fix round) or `STATUS: BLOCKED <reason>`. Write it last, only when
  everything above is true. A report without it is treated as unfinished work after a restart.

QA writes `_workspaces/reports/<ID>-qa.md`: one `## Round <n>` section per gate, tests it added under
its own `## Files changed`, and as the last line `VERDICT: PASS round=<n>` or `VERDICT: FAIL round=<n>`
(the concrete failures listed above it). `accept` reads the last `VERDICT:` line of the file.

## Lifecycle

1. `start` (orchestrator) → spawn the owner agent with the task file path.
2. Owner implements, runs the full suite in its snapshot, writes the report ending with `STATUS:`.
3. Orchestrator runs `snapshot` and spawns the gate agent → `<ID>-qa.md`.
4. PASS → `accept` (verdict check, change-set check, move to `done/`, one local commit; never push).
   FAIL → findings go back to the owner (up to 2 fix rounds, the second on Opus) → gate again.
   Still failing, or the owner reports a spec contradiction → `block` with the reason; the architect
   resolves it (ADR, split, prerequisite or rescope) under the unblock lock.
5. Interrupted work (session restart, crash, hung agent): `recover <ID>` decides from
   `autopilot.json` stage/round, the report's `STATUS:` line and the QA `VERDICT:` — `accept`, `qa`,
   `fix <n>`, `block` or `requeue`. A requeued task keeps its report/QA files; the next agent reads
   them and continues rather than restarting from scratch.

Attempts: `start` counts one attempt; a charged `requeue` blocks the task at the 3rd attempt (crash
loops go to the architect). Infrastructure failures (rate limit, quota, API or tool error) use
`requeue --infra`, restarts and hung-but-progressing agents `requeue --no-attempt`: neither is charged.
`unblock` resets attempts and counts a cycle; after 2 unblock cycles, or 2 failed unblock agents, the
task is `parked` (exit 4) and listed in `_workspaces/STUCK.md` for the owner instead of looping.

Commit message (produced by `accept`): `T034: Struct + layout engine` + body + `Co-Authored-By`
trailer (override with `AXIOM_COMMIT_TRAILER`). Architect work outside a task (unblock, phase review,
audit fixes) is committed with `taskctl.py commit-report <report.md> --subject "arch: ..."`, which
stages exactly the report's `## Files changed` plus the board. The owner's files under `docs/` and
git-ignored paths are never staged by these commands. `.claude/hooks/guard.py` is the PreToolUse
safety hook (enabled in `.claude/settings.json` by the owner): it refuses any tool call that would
edit `docs/`, stage it, or push, and nothing else. `.claude/settings.json` itself (permissions,
hooks) is never changed by an agent: propose the change in a file and let the owner apply it
(`harness_check.py --settings <file>` verifies a proposal).

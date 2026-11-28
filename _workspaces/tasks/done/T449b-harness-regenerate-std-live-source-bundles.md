---
id: T449b
title: Harness — regenerate std live-source test bundles (tests/std/**, tests/conformance/**) like selfhost bundles
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T449a]
priority: 25
status: done
attempts: 1
paths: [.claude/skills/axiom-tasks/scripts/bundles.py, tests/std/async/executor/gen_tests.py, tests/std/async/structured/gen_tests.py, tests/std/async/waker/gen_tests.py, tests/std/async/waker_qa/gen_tests.py, tests/std/channel/gen_tests.py, tests/std/fiber/gen_tests.py, tests/std/sync/gen_tests.py, tests/std/thread/native_panic_hook/gen_tests.py]
locks: [.claude/skills/axiom-tasks/scripts/selftest.py, .claude/skills/axiom-tasks/scripts/taskctl.py, .claude/skills/axiom-tasks/SKILL.md, .claude/skills/axiom-testing/SKILL.md]
spec: [spec/SPEC-20-selfhost.md]
covers: [REQ-TST-072]
started: 2026-11-28 21:40:20
finished: 2026-11-28 22:00:49
---
# T449b — Harness: regenerate std live-source test bundles automatically

## Why
Owner decision 2026-11-17 made the `tests/selfhost/**/gen_*.py` bundles harness-owned: `taskctl snapshot` and
`taskctl accept` regenerate them, so they can never be committed stale. Several generators outside
`tests/selfhost` follow the same pattern — they concatenate live `std/` sources into committed `.ax` bundles and
carry a `check_*_bundles.test` freshness check — but the harness does not know them. Result: any std change
silently stales them and the freshness checks fail at HEAD for every later gate (4 ids found by the T427 gate,
fixed once by T449a). This task removes the class of failure instead of re-fixing it each time.

## Scope
1. Inventory every committed-bundle generator outside `tests/selfhost` (at least `tests/std/async/{executor,
   structured,waker,waker_qa}`, `tests/std/{channel,fiber,sync}`, `tests/std/thread/native_panic_hook`; check
   `tests/conformance/**/gen_tests.py` and `tests/perf/**/gen_tests.py` too). Classify each: (a) bundles live
   `std/`/`compiler/` sources (harness-owned, regenerated), or (b) produces static fixtures independent of live
   sources (stays task-owned, excluded). Record the table in the report.
2. Extend `bundles.py` so class (a) generators are part of `regen`/`check`/`list` (explicit allowlist or a
   discoverable marker — choose the one that cannot pick up an unrelated script by accident). Keep the
   determinism contract of the module docstring (pure function of the tree, no compiler run in write mode,
   `wrote <path>` lines define the generated set). Adapt a class (a) generator only where needed to meet that
   contract (print `wrote <path>`, resolve ROOT from its own location, no compiler call in write mode).
3. Keep one manifest (`tests/selfhost/generated-files.txt`) or add a second one; either way `taskctl accept`
   stages and REGATE-checks the new files exactly as it does the selfhost ones, and retired files are removed.
4. Add `selftest.py` cases: a std change that alters a class (a) bundle is regenerated in the snapshot and staged by
   accept; a class (b) generator is never run.
5. Update `.claude/skills/axiom-tasks/SKILL.md` and `.claude/skills/axiom-testing/SKILL.md` (agents do not
   hand-edit or list these bundles in `## Files changed`, same as selfhost bundles).

## Acceptance
- [ ] `python bundles.py check` passes on HEAD and covers every class (a) generator; `list` shows their outputs.
- [ ] `python .claude/skills/axiom-tasks/scripts/selftest.py` passes, including the new cases.
- [ ] `harness_check.py` passes.
- [ ] Simulated check: touching a bundled std file in a scratch tree and running `bundles.py regen` refreshes
      the affected class (a) bundles so their `check_*_bundles` tests pass.
- [ ] Report `_workspaces/reports/T449b-report.md` (inventory table, exact `## Files changed`). The orchestrator adds
      the CLAUDE.md history row on accept.

## Log
- 2026-11-25 created by architect (triage after T427 accept, `_workspaces/reports/triage-2026-11-25-T427.md`)
- 2026-11-25 priority 120 -> 25 by architect (T428 triage: T428d/T428e/T428f edit std/async and wait for the harness-owned std bundle regeneration)
- 2026-11-28 21:40:20 started (attempt 1) axiom-qa
- 2026-11-28 22:00:49 accepted by QA -> done

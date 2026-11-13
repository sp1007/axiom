---
id: T439
title: Baseline fix — tools/tests/gatecheck self-test test_check_without_command_blocks
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 18
status: todo
attempts: 0
paths: [tools/gatecheck.py, tools/tests/gatecheck]
locks: [_workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/decisions/ADR-0005-plan-structure-corrections.md]
covers: [REQ-TST-068]
---
# T439 — Baseline fix: gatecheck self-test

## Goal
`python tools/tests/gatecheck/run_selftests.py` passes (33 tests, 0 failures) so `tools/taskgate.py` no longer
reports gatecheck as KNOWN (ADR-0042 §1, T437a-qa R2).

## Scope
- Observed at HEAD (T437a-qa, `git archive bed3d915 tools`): `test_gatecheck.GatecheckTest.test_check_without_command_blocks`
  fails with a `TypeError ... NoneType` assertion.
- Diagnose whether the test or `tools/gatecheck.py` is wrong against the phase-gate rule R9 (a gate without a command
  must be BLOCKED, never PASS). Fix the wrong side; do not weaken the test's intent.
- Remove the `T439` line from `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] `python tools/tests/gatecheck/run_selftests.py` -> 0 failures, 0 errors; the formerly failing test asserts the
  BLOCKED outcome explicitly.
- [ ] `python tools/taskgate.py --task T439 ...` shows `tools/tests/gatecheck PASS` (not KNOWN), exit 0.
- [ ] Report `_workspaces/reports/T439-report.md` with exact `## Files changed`.

## Out of scope
- `tools/axtest.py`, `tools/taskgate.py`, `.claude/`, `docs/`.

## Notes
- Reviewer is the architect because the owner is axiom-qa (reviewer is never the owner).

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §1, architect inbox 1)

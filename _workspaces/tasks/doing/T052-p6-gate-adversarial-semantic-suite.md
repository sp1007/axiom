---
id: T052
title: P6 gate: adversarial semantic suite
phase: P6-ownership
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T051, T052a, T052b, T126a]
priority: 72
status: doing
attempts: 1
paths: [tests, spec, _workspaces/tasks/done]
spec: [0026, 0022, 0019, 0020, 0028, 0017]
started: 2026-10-12 09:20:39
unblocks: 1
---
# T052 — P6 gate: adversarial semantic suite

## Goal
Attack the ownership/capability implementation with the adversarial cases from the specs.

## Scope
- Port 0026 adversarial tests + relevant 0022 stress tests into canonical syntax; report every divergence as finding or spec gap.

## Implementation Plan
1. Update `tests/conformance/stress/e003.ax` to either expect `AX_CAP_CONFLICT_MUT` or use explicit block scoping for the view, as per ADR-0006.
2. Fix board hygiene issues preventing `gatecheck.py`, `reqcov.py` and `harness_check.py` from passing:
   - Update `spec/invariants.md` to change `since: T046` to `since: T121` (T046 was superseded).
   - Update `spec/requirements/CATALOG.md` (or `COVERAGE.md`) to change `T049` to `T127` in `REQ-MIR-001`.
   - Update `_workspaces/tasks/done/T052a-fix-partial-moves.md` to add `gate_model: opus`.
   - Remove `// xfail: T130` from `tests/run/drop/qa_array_drop.ax`.
3. Re-run the test suite and gate scripts to verify everything passes.

## Acceptance
- [ ] The whole suite passes. A divergence that is a spec gap gets an architect ADR and an `xfail: <task-id>` entry; an implementation bug blocks the gate until its fix task is done (0264 §20: PASS or BLOCKED, never "almost done").
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T052-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-12 08:49:03 started (attempt 1) 
- 2026-10-12 08:56:03 block: partial move and last-use bugs
- 2026-10-12 09:20:31 unblocked (cycle 1) 
- 2026-10-12 09:20:39 started (attempt 1) 

---
id: T019
title: THIR → MIR builder (subset)
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
depends: [T018]
priority: 32
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/build, tests/mir/build]
spec: [0161, tasks/0364, tasks/0539, 0041]
---
# T019 — THIR → MIR builder (subset)

## Goal
Lower typed HIR of the subset into MIR CFGs.

## Scope
- Locals/temps, arithmetic, comparisons, short-circuit via CFG, if/while/loop/break/continue/return, calls, evaluation order per SPEC-03.

## Acceptance
- [ ] Golden MIR tests incl. first MIR test (`return 40 + 2` → const/const/add/return structure).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T019-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

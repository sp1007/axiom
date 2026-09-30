---
id: T069
title: core library v1 (Axiom source)
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T062]
priority: 100
status: todo
attempts: 0
paths: [std/core, tests/std/core]
spec: [0169, 0170, 0219, 0303, 0305, tasks/0353]
---
# T069 — core library v1 (Axiom source)

## Goal
The OS-independent core every Axiom program can use.

## Scope
- Primitive methods (min/max/abs/checked_*/wrapping_*), Option/Result combinators, cmp/ops traits, mem (size_of, align_of, swap, replace, take), intrinsics declarations, panic/assert/debug_assert.

## Acceptance
- [ ] tests/std/core run tests (interp + native).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T069-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

---
id: T039
title: Option/Result lang items + `?` operator
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T038]
priority: 59
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, std/core/prelude, tests/run/result, tests/ui/result]
spec: [0269, 0111, 0107, 0222, tasks/0288]
---
# T039 — Option/Result lang items + `?` operator

## Goal
Error handling core: Option/Result in the prelude and `?` lowering.

## Scope
- Prelude source (Axiom) or built-in lang items for Option/Result (non-generic special-casing allowed until generics land — mark BOOTSTRAP-SHORTCUT and file follow-up for T054), `?` on Option/Result with return-type compatibility checks.

## Acceptance
- [ ] run tests for propagation paths; ui tests for `?` in non-Result fn.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T039-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

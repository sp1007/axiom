---
id: T039
title: Option/Result lang items + `?` operator
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T038b]
priority: 59
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/result, tests/ui/result, bootstrap/axiom0/src/hir]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [tasks/0269, 0111, 0107, 0222, tasks/0288]
started: 2026-10-10 09:12:39
finished: 2026-10-10 10:19:14
---
# T039 — Option/Result lang items + `?` operator

## Goal
Error handling core: Option/Result in the prelude and `?` lowering.

## Scope
- Built-in, non-generic lang items for Option/Result (ADR-0006 §4; mark `BOOTSTRAP-SHORTCUT` — T054b replaces them by generic enums in std, loaded through the prelude mechanism of T060), `?` on Option/Result with return-type compatibility checks.

## Acceptance
- [ ] run tests for propagation paths; ui tests for `?` in non-Result fn.
- [ ] `if let` / `while let` over Option (moved here from T038).
- [ ] Run tests carry `// native-after: T040` (removed by T040).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T039-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 09:12:39 started (attempt 1) 
- 2026-10-10 10:19:14 accepted by QA -> done

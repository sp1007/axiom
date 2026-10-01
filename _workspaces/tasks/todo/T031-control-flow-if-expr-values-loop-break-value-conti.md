---
id: T031
title: Control flow: if-expr values, loop/break value, continue, blocks, never
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T030]
priority: 51
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/cfg, tests/ui/cfg]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0063, 0041, 0113, tasks/0391, tasks/0617]
---
# T031 — Control flow: if-expr values, loop/break value, continue, blocks, never

## Goal
Expression-oriented control flow with correct typing.

## Scope
- if as expression (branch type unification), block values, loop with `break value`, continue, labelled loops (`break`/`continue` to a label; ADR-0004 §7), `never` type from return/break/panic, unreachable code warnings.

## Acceptance
- [ ] run + ui tests in interp mode; run tests carry `// native-after: T033` (removed by T033).
- [ ] At least one positive run test and one negative ui test per Scope bullet; the report maps each bullet to its test files (QA checks the map).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T031-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

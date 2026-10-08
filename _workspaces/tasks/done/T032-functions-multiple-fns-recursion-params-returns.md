---
id: T032
title: Functions: multiple fns, recursion, params, returns
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T031]
priority: 52
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/fn, tests/ui/fn]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0069, tasks/0266, tasks/0284]
covers: [REQ-CONC-001, REQ-CONC-002]
started: 2026-10-08 10:51:13
finished: 2026-10-08 11:25:47
---
# T032 — Functions: multiple fns, recursion, params, returns

## Goal
Full function semantics in the oracle.

## Scope
- Order-independent item use, recursion/mutual recursion, many params, unit fns, early return, argument evaluation order.

## Acceptance
- [ ] run + ui tests in interp mode; run tests carry `// native-after: T033` (removed by T033).
- [ ] At least one positive run test and one negative ui test per Scope bullet; the report maps each bullet to its test files (QA checks the map).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T032-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Direct calls and simple recursion already work since T019/T021; this task adds what Scope lists and re-tests the rest, it does not re-implement it.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:55 covers += REQ-CONC-001, REQ-CONC-002 (metadata only)
- 2026-10-08 10:51:13 started (attempt 1) T032-impl
- 2026-10-08 11:25:47 accepted by QA -> done

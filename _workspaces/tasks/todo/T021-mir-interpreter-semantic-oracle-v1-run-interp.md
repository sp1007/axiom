---
id: T021
title: MIR interpreter (semantic oracle) v1 + `run --interp`
phase: P3-semantic-core
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T020]
priority: 34
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/interp, tests/run/basic]
spec: [0025, 0031, 0145, spec/SPEC-03-core-semantics.md]
---
# T021 — MIR interpreter (semantic oracle) v1 + `run --interp`

## Goal
Execute verified MIR with exact Axiom semantics; exit code = main's result.

## Scope
- Value model independent of host C behaviour (explicit overflow/div/shift rules), call stack, abort-panic with SPEC-03 exit code, step limit for tests.

## Acceptance
- [ ] run tests: exit 42, arithmetic, branches, loops, recursion (fib), overflow trap, division by zero behaviour.
- [ ] `axiom0 run --interp` works; runner's interp mode enabled.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T021-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

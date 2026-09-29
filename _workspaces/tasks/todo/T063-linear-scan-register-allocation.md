---
id: T063
title: Linear-scan register allocation
phase: P8-backend
owner: axiom-backend
reviewer: axiom-qa
depends: [T062]
priority: 90
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/target/x64/regalloc, bootstrap/axiom0/src/target/x64, tests/mc/regalloc]
spec: [0182, 0235, 0252, tasks/0557]
---
# T063 — Linear-scan register allocation

## Goal
Replace fixed-register baseline at -O1 with linear scan.

## Scope
- Liveness, intervals, linear scan with ABI-driven register classes, spill/reload, callee-saved save/restore, call clobbers; -O0 keeps baseline.

## Acceptance
- [ ] Differential green at -O0/-O1; code-size/perf improvement recorded via tools/perf.py.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T063-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

---
id: T063
title: E15.8 Linear-scan register allocation
phase: P15-optimizer-2-0
owner: axiom-backend
reviewer: axiom-qa
depends: [T215]
priority: 90
status: todo
attempts: 0
paths: [compiler/target/x64/regalloc, tests/mc/regalloc]
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
- Roadmap epic E15.8 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; the phase planning task may split it, keeping this id for the first slice.
- First task of P15: improves the speed of code produced by axiomc itself.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

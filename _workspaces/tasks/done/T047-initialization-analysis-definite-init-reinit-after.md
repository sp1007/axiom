---
id: T047
title: Initialization analysis (definite init, reinit after move)
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T121]
priority: 67
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own/init, tests/ui/init, tests/run/init, tests/ui/own, tests/ui/vars]
locks: [bootstrap/axiom0/src/diag/codes/INIT.def, bootstrap/axiom0/src/own/own.c, bootstrap/axiom0/src/types/typeck.c, bootstrap/axiom0/src/verify/verify.c, bootstrap/axiom0/src/target/x64/verify/verify.c, tests/ui/own/uninit.ax, tests/ui/vars/uninit_use.ax]
spec: [spec/SPEC-10-ownership.md, tasks/0394]
covers: [REQ-MOD-001, REQ-MOD-002]
started: 2026-10-10 18:19:09
unblocks: 1
finished: 2026-10-10 18:48:48
---
# T047 — Initialization analysis (definite init, reinit after move)

## Goal
Definite initialization across CFG including loops and conditional moves.

## Scope
- Uninit use errors, conditional init, reinitialisation of moved places, struct field init.

## Acceptance
- [ ] Every test-matrix row tagged T047 passes. Run tests carry `// native-after: T051`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T047-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:24:22 covers += REQ-MOD-001, REQ-MOD-002 (metadata only)
- 2026-10-10 18:08:43 started (attempt 1) T047-impl
- 2026-10-10 18:16:02 block: T047 lacks required paths to own.c, typeck.c, and verify.c to integrate the analysis and remove legacy checks
- 2026-10-10 18:17:42 unblocked (cycle 1) 
- 2026-10-10 18:19:09 started (attempt 1) T047-impl
- 2026-10-10 18:48:48 accepted by QA -> done

---
id: T124
title: "Basic capability tracking & syntax for views"
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T047, T123]
priority: 67
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own/cap, bootstrap/axiom0/src/types, bootstrap/axiom0/src/own, bootstrap/axiom0/src/syntax]
locks: [bootstrap/axiom0/src/diag/codes/CAP.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [spec/SPEC-11-capability.md, 0177, 0021, 0028, tasks/0395]
started: 2026-10-10 19:35:24
finished: 2026-10-10 19:52:38
---
# T124 — Basic capability tracking & syntax for views

## Goal
Implement foundational view tracking in own.c and syntax/typeck.

## Scope
- Implement `ax_mir_cap_tracker` for basic capability tracking.
- Integrate into `ax_own_check` and `syntax/typeck`.
- This is a prerequisite split out of T048.

## Acceptance
- [ ] View capability structures are present and build warning-free.
- [ ] Stubs for conflict detection to be fleshed out in T125.
- [ ] Report `_workspaces/reports/T124-report.md` with exact `## Files changed`.

## Log
- 2026-10-10 19:35:24 started (attempt 1) T124-impl
- 2026-10-10 19:52:38 accepted by QA -> done

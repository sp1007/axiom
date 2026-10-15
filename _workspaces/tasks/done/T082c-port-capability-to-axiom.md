---
id: T082c
title: Port capability analysis (views & mut_views) to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082b]
priority: 116
status: done
attempts: 1
paths: [compiler/own/cap.ax, tests/selfhost/cap]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-OWN-338]
started: 2026-10-15 20:06:26
finished: 2026-10-15 20:06:27
---
# T082c — Port capability analysis (views & mut_views) to Axiom

## Goal
Port capability analysis for immutable `view` and mutable `mut_view` (`compiler/own/cap.ax`) from C to Axiom.

## Scope
- Port capability tracking, view lifetime boundaries, borrow conflict checking, and aliasing rules.
- Rejection of overlapping mutable views or modifications while a view is active.
- Unit tests under `tests/selfhost/cap/`.

## Acceptance
- [ ] Capability analysis implemented in `compiler/own/cap.ax` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Capability conflict diagnostics match `axiom0` on error fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082c-report.md` with exact `## Files changed`.

## Out of scope
- Drop elaboration (handled in T082d).

## Notes
- `model: opus`: Capability tracking requires semantic precision (model policy).
- Sub-task of T082 split per ADR-0005 §8 and SPEC-20 §4.6.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-15 20:06:26 started (attempt 1) axiom-stdlib
- 2026-10-15 20:06:27 accepted by QA -> done

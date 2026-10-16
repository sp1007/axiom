---
id: T082d
title: Port drop elaboration and cleanup edges to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082c]
priority: 116
status: done
attempts: 1
paths: [compiler/mir/drop.ax, tests/selfhost/drop]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRP-183]
started: 2026-10-16 23:51:50
finished: 2026-10-17 02:30:22
---
# T082d — Port drop elaboration and cleanup edges to Axiom

## Goal
Port drop elaboration, drop flag tracking, and cleanup blocks (`compiler/mir/drop.ax`) from C to Axiom.

## Scope
- Port drop flag synthesis for conditionally moved variables.
- Port insertion of drop terminators at scope exit, returns, break, and panic edges.
- Port synthesis of destructor calls for compound structures and generic containers.
- Unit tests under `tests/selfhost/drop/`.

## Acceptance
- [ ] Drop elaboration implemented in `compiler/mir/drop.ax` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Elaborated drop calls and cleanup CFG blocks match `axiom0 inspect --emit=mir`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082d-report.md` with exact `## Files changed`.

## Out of scope
- MIR verification (handled in T082e).

## Notes
- `model: opus`: Drop elaboration requires semantic precision (model policy).
- Sub-task of T082 split per ADR-0005 §8 and SPEC-20 §4.6.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-16 22:22:23 started (attempt 1) T082d-impl
- 2026-10-16 23:51:04 requeue: session limit 429, resets 23:50; work kept in files (infrastructure failure: attempt refunded)
- 2026-10-16 23:51:50 started (attempt 1) T082d-impl
- 2026-10-17 02:30:22 accepted by QA -> done

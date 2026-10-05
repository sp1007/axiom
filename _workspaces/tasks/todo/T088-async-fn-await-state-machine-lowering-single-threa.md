---
id: T088
title: E11.4 async fn / await: state-machine lowering + single-thread executor
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T211]
priority: 130
status: todo
attempts: 0
paths: [compiler/mir/async, compiler/types, std/async, tests/run/async]
spec: [0093, tasks/0275, tasks/0297, 0202, 0248]
covers: [REQ-ASY-167, REQ-ASY-168]
---
# T088 — async fn / await: state-machine lowering + single-thread executor

## Goal
Async per spec without mandatory runtime.

## Scope
- Future lang item, async fn → state machine in MIR, await points with drop/cleanup correctness, minimal executor in std.

## Acceptance
- [ ] run tests (interp + native).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T088-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Roadmap epic E11.4. Implemented in `compiler/` (Axiom) / `std/` — axiom0 is frozen after T087 (ROADMAP R3).
- The P11/P23 planning task may split this task further; keep its id for the first slice.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:54 covers += REQ-ASY-167, REQ-ASY-168 (metadata only)

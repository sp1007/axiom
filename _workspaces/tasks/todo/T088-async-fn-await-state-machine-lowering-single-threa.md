---
id: T088
title: async fn / await: state-machine lowering + single-thread executor
phase: P11-v1
owner: axiom-semantics
reviewer: axiom-qa
depends: [T075]
priority: 130
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/async, bootstrap/axiom0/src/types, std/async, tests/run/async]
spec: [0093, 0275, tasks/0297, 0202, 0248]
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
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

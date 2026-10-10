---
id: T046
title: Place model + move/copy analysis (use-after-move, partial moves)
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T044, T045]
priority: 66
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own, tests/ui/own, tests/run/own]
locks: [bootstrap/axiom0/src/diag/codes/MOVE.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [spec/SPEC-10-ownership.md, 0160, 0176, tasks/0394, tasks/0503]
started: 2026-10-10 13:47:45
superseded_by: T120
finished: 2026-10-10 13:55:08
---
# T046 — Place model + move/copy analysis (use-after-move, partial moves)

## Goal
Ownership dataflow over MIR places.

## Scope
- Copy classification (builtin types + `@derive(Copy)`, recognised here as a built-in marker — ADR-0006 §3; T056 generalises derive); dataflow of UNINIT/OWNED/PARTIAL/MOVED per place; diagnostics AX_MOVE_USE_AFTER_MOVE (with 'moved here' label), partial-move rules, moves in loops/branches.
- Registers the ownership stage in `src/driver/pipeline.c` once (`own` entry point); T047, T048 and T048b add their analyses inside that stage and do not touch the driver.

## Acceptance
- [ ] Every SPEC-10 test-matrix row tagged T046 has passing positive + negative tests. Run tests carry `// native-after: T051` (removed by T051).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T046-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 13:47:45 started (attempt 1) T046-impl
- 2026-10-10 13:53:48 block: Data flow logic and tests are yet to be implemented.
- 2026-10-10 13:55:08 superseded by T120 -> done (no code of its own)

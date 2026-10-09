---
id: T035b
title: Structs layout and oracle execution
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T035a]
priority: 55
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types/layout, bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/struct, tests/unit/types]
spec: [0059, 0081, 0043, tasks/0267, tasks/0281, 0009]
started: 2026-10-09 12:13:19
superseded_by: T035d
finished: 2026-10-09 12:17:21
---
# T035b — Structs layout and oracle execution

## Goal
Aggregate data through the oracle with a layout engine.

## Scope
- Layout (size/align/field offsets, default repr rules per spec), `@repr(C)` layout. MIR emission and oracle interpretation for structs.

## Acceptance
- [ ] run tests (0263 §37 Point test) + layout unit tests. Run tests carry `// native-after: T037`.
- [ ] Full test suite passes.
- [ ] Report `_workspaces/reports/T035b-report.md`.

## Notes
- Second part of original T035.

## Log
- 2026-10-09 12:13:19 started (attempt 1) T035b-impl
- 2026-10-09 12:16:37 block: Splitting due to extensive refactor
- 2026-10-09 12:17:21 superseded by T035d -> done (no code of its own)

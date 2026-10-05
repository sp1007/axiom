---
id: T064
title: E15.4 Optimizer ladder 2: copy propagation, inlining, SROA
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215]
priority: 91
status: todo
attempts: 0
paths: [compiler/opt, tests/opt2]
spec: [0165, 0226, tasks/0401, tasks/0399]
covers: [REQ-TYP-001, REQ-TYP-002, REQ-TYP-003, REQ-TYP-004, REQ-TYP-005, REQ-TYP-006]
---
# T064 — Optimizer ladder 2: copy propagation, inlining, SROA

## Goal
Meaningful MIR optimizations with legality from ownership facts.

## Scope
- Copy propagation, small-function inlining, scalar replacement of aggregates, simple bounds-check elimination, return-slot construction (0152 §74).

## Acceptance
- [ ] Differential green; perf numbers recorded.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T064-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- `paths` are provisional: T076 fixes the `compiler/<module>` layout and re-paths this task (ADR-0005 §8).
- Roadmap epic E15.4 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; the phase planning task may split it, keeping this id for the first slice.
- 
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:24 covers += REQ-TYP-001, REQ-TYP-002, REQ-TYP-003, REQ-TYP-004, REQ-TYP-005, REQ-TYP-006 (metadata only)

---
id: T120
title: Place model, copy classification, pipeline registration (T046 split)
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T044, T045]
priority: 66
status: done
attempts: 2
paths: [bootstrap/axiom0/src/own, bootstrap/axiom0/src/diag/codes/MOVE.def, bootstrap/axiom0/src/driver/pipeline.c, bootstrap/axiom0/src/driver/driver.h, tests/unit/own]
locks: [bootstrap/axiom0/src/diag/codes/MOVE.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [spec/SPEC-10-ownership.md, spec/decisions/ADR-0019-split-t046-move-analysis.md]
started: 2026-10-10 15:37:34
finished: 2026-10-10 16:03:50
---
# T120 — Place model, copy classification, pipeline registration (T046 split)

## Goal
Implement place model basics, copy classification, and ownership stage registration.

## Scope
- Copy classification (builtin types + `@derive(Copy)`).
- Registers the ownership stage in `src/driver/pipeline.c` once (`own` entry point).
- Setup of structures in `own.c`, `own.h`, and basic diagnostic codes in `MOVE.def`.
- No data flow analysis yet.

## Acceptance
- [ ] Structures and basic ownership pipeline pass build.
- [ ] Build warning-free; archcheck clean (once available).
- [ ] Full test suite passes.

## Log
- 2026-10-10 15:37:34 started (attempt 2) T120-impl
- 2026-10-10 16:03:50 accepted by QA -> done

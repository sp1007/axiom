---
id: T122
title: Add AxLocation tracking to MIR
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: []
priority: 65
status: done
attempts: 1
paths: [bootstrap/axiom0/src/mir]
locks: []
started: 2026-10-10 16:33:03
finished: 2026-10-10 17:22:15
---
# T122 — Add AxLocation tracking to MIR

## Goal
Add location tracking (AxLocation) to MIR statements and operands to support accurate diagnostics in dataflow passes.

## Scope
- Modify MIR data structures (statements, operands) to store `AxLocation`.
- Update MIR builder to extract locations from HIR and attach them to MIR elements.
- Update MIR printer and parser as necessary.

## Acceptance
- MIR correctly carries location tracking information for statements and operands.
- Tests pass and compiler builds without warnings.

## Log
- 2026-10-10 16:33:03 started (attempt 1) T122-impl
- 2026-10-10 17:22:15 accepted by QA -> done

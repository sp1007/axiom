---
id: T127
title: MIR Infrastructure for Drop
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T048b]
priority: 69
status: todo
paths: [bootstrap/axiom0/src/mir/drop, bootstrap/axiom0/src/mir/build, bootstrap/axiom0/src/interp, tests/run/drop, tests/ui/drop, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/lir, bootstrap/axiom0/src/own/own.c, bootstrap/axiom0/src/own/cap/cap.c]
locks: [bootstrap/axiom0/src/mir/mir.h, bootstrap/axiom0/src/mir/parse.c, bootstrap/axiom0/src/mir/print.c, bootstrap/axiom0/src/driver/pipeline.c]
attempts: 0
started: 2026-10-11 08:28:18
unblocks: 1
---
# T127 — MIR Infrastructure for Drop

## Goal
Extend MIR data structures to support drop statements, drop flags, and drop terminators.

## Scope
- Update `AxMirBb` to include `stmt_cap` or appropriate structures to handle larger statement lists.
- Introduce drop terminators and drop statements in the MIR definition.
- Establish the structural foundation for drop elaboration without implementing complex elaboration logic.

## Acceptance
- MIR data structures correctly support drop constructs.
- Builds without GCC compilation errors.

## Notes
- Created as part of splitting T049 (ADR-0027).

## Log
- 2026-10-11 08:28:18 started (attempt 1) T127-impl
- 2026-10-11 09:11:06 block: QA failed 3 times: C-driver MIR parse test string uses wrong syntax (fn main instead of mir_body), causing ICE.
- 2026-10-11 09:14:22 unblocked (cycle 1) 

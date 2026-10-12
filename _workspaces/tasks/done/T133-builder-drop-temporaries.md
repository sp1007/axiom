---
id: T133
title: Drop Elaboration for Temporaries
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T130, T131]
priority: 70
status: done
paths: [bootstrap/axiom0/src/mir/build, tests/run/drop]
locks: [bootstrap/axiom0/src/diag/codes/VERIFY.def]
attempts: 1
started: 2026-10-12 07:07:16
finished: 2026-10-12 07:57:51
---
# T133 — Drop Elaboration for Temporaries

## Goal
Ensure `builder.c` correctly emits drops for temporary variables (`AX_MIR_LOCAL_TMP`) holding values of types that require dropping.

## Scope
- Modify MIR builder to track temporary variables that hold drop-requiring types (e.g. function return values, intermediate expressions).
- Emit appropriate `drop(tmp)` terminator/instruction for these temporaries before they go out of scope, unless their ownership has been moved.

## Acceptance
- [ ] Temporaries are correctly dropped in generated MIR.
- [ ] Tests verify that temporaries requiring drop are correctly cleaned up.

## Notes
- Created via ADR-0033. Verifier MUST NOT exempt temporaries from missing drop checks, so this task must properly generate drops.

## Log
- 2026-10-12 07:07:16 started (attempt 1) 
- 2026-10-12 07:57:51 accepted by QA -> done

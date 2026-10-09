---
id: T038
title: Enums + match + exhaustiveness
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T036]
priority: 58
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/driver, bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/types/match, tests/run/enum, tests/ui/enum, tests/mir/build, bootstrap/axiom0/src/target, bootstrap/axiom0/src/lir]
locks: [bootstrap/axiom0/src/diag/codes/PAT.def, bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0065, tasks/0268, tasks/0392, tasks/0504]
---
# T038 - Enums + match + exhaustiveness

## Acceptance
All tests pass.

## Log
- 2026-10-09 18:36:09 requeue: Overlapping paths with T037, waiting for T037 to finish (infrastructure failure: attempt refunded)

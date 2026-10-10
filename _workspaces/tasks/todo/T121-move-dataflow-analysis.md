---
id: T121
title: Move dataflow analysis (use-after-move, partial moves) (T046 split)
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T120]
priority: 66
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/own, tests/ui/own, tests/run/own]
locks: []
spec: [spec/SPEC-10-ownership.md, spec/decisions/ADR-0019-split-t046-move-analysis.md]
---
# T121 — Move dataflow analysis (use-after-move, partial moves) (T046 split)

## Goal
Ownership dataflow over MIR places.

## Scope
- Dataflow of UNINIT/OWNED/PARTIAL/MOVED per place.
- Diagnostics AX_MOVE_USE_AFTER_MOVE (with 'moved here' label), partial-move rules, moves in loops/branches.

## Acceptance
- [ ] Every SPEC-10 test-matrix row tagged T121 has passing positive + negative tests. Run tests carry `// native-after: T051` (removed by T051).
- [ ] Full test suite passes; build warning-free; archcheck clean.

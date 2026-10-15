---
id: T081c
title: Port type checker and inference engine to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T081b]
priority: 115
status: done
attempts: 1
paths: [compiler/types/typeck.ax, tests/selfhost/typeck]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-TYP-355]
started: 2026-10-15 12:07:05
finished: 2026-10-15 12:07:19
---
# T081c — Port type checker and inference engine to Axiom

## Goal
Port the bidirectional type checker, type inference engine, and pattern exhaustiveness checking (`compiler/types/typeck.ax`) from C to Axiom.

## Scope
- Port bidirectional type checking, constraint solving, unification, and coercions.
- Port match pattern exhaustiveness checking and useless pattern detection.
- Port method call resolution and operator overloading type checking.
- Unit tests under `tests/selfhost/typeck/`.

## Acceptance
- [ ] Type checker implemented in `compiler/types/typeck.ax` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Type inference and diagnostic error codes match `axiom0` on typeck error fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T081c-report.md` with exact `## Files changed`.

## Out of scope
- Ownership and borrow analysis (handled in T082).

## Notes
- `model: opus`: Porting the type checker requires semantic precision (model policy).
- Sub-task of T081 split per ADR-0005 §8 and SPEC-20 §4.5.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-15 12:07:05 started (attempt 1) axiom-semantics
- 2026-10-15 12:07:19 finished without commit (manual) -> done; run `taskctl commit` next

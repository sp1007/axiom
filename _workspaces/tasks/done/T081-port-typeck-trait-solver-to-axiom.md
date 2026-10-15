---
id: T081
title: Port typeck + trait solver to Axiom (integration + differential typeck)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T081a, T081b, T081c]
priority: 115
status: done
attempts: 1
paths: [compiler/typeck_traits, tests/selfhost/typeck_traits]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-GEN-100, REQ-TRT-139, REQ-TYP-354, REQ-TYP-355]
started: 2026-10-15 20:02:36
finished: 2026-10-15 20:02:37
---
# T081 — Port typeck + trait solver to Axiom (integration + differential typeck)

## Goal
Integrate typeck and trait solver in Axiom and run differential type checking against `axiom0`.

## Scope
- Integrate `compiler/types` and `compiler/traits`.
- Differential test harness comparing typed AST/HIR dumps and typeck diagnostics against `axiom0` across the entire tests corpus.
- Verification of generic monomorphization, trait bounds, and exhaustiveness analysis.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T081a, T081b, T081c integrated and passing differential checks.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T081-report.md` with exact `## Files changed`.

## Out of scope
- MIR building (handled in T082).

## Notes
- `model: opus`: Porting the type checker and trait solver requires semantic precision (model policy).
- Group integration task for T081a, T081b, T081c per ADR-0005 §8 and SPEC-20 §4.5.
- Exact differential artefact: `inspect --emit=thir` and type error diagnostics.
- Harness entry: `tests/selfhost/typeck_traits`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-15 20:02:36 started (attempt 1) axiom-stdlib
- 2026-10-15 20:02:37 accepted by QA -> done

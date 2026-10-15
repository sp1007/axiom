---
id: T081b
title: Port trait solver & monomorphization engine to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T081a]
priority: 115
status: done
attempts: 1
paths: [compiler/traits, tests/selfhost/traits]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-GEN-100, REQ-TRT-139]
started: 2026-10-15 12:06:35
finished: 2026-10-15 12:06:55
---
# T081b — Port trait solver & monomorphization engine to Axiom

## Goal
Port trait solver, static dispatch resolution, and generic monomorphization (`compiler/traits/`) from C to Axiom.

## Scope
- Port trait definitions, impl block registration, associated type resolution, and static method dispatch.
- Port generic type substitution, mangling, and monomorphization instance cache.
- Unit tests under `tests/selfhost/traits/`.

## Acceptance
- [ ] Trait solver and monomorphization implemented in `compiler/traits/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Monomorphized instance sets and method dispatch agree with `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T081b-report.md` with exact `## Files changed`.

## Out of scope
- General expression type inference (handled in T081c).

## Notes
- `model: opus`: Porting trait solver requires semantic precision (model policy).
- Sub-task of T081 split per ADR-0005 §8 and SPEC-20 §4.5.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-15 12:06:35 started (attempt 1) axiom-semantics
- 2026-10-15 12:06:55 finished without commit (manual) -> done; run `taskctl commit` next

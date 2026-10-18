---
id: T083
title: Port interpreter + optimizer to Axiom (integration + differential)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082, T083a, T083b]
priority: 117
status: done
attempts: 1
paths: [compiler/interp_opt, tests/selfhost/interp_opt]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-OPT-387, REQ-OPT-388, REQ-OPT-389]
started: 2026-10-18 15:12:25
finished: 2026-10-19 03:16:37
---
# T083 — Port interpreter + optimizer to Axiom (integration + differential)

## Goal
Integrate interpreter and optimizer in Axiom and run differential execution and optimization testing against `axiom0`.

## Scope
- Integrate `compiler/interp` and `compiler/opt`.
- Differential test harness comparing program execution results and optimized MIR dumps with `axiom0`.
- Verification of -O0 and -O1 semantic equivalence across the entire tests corpus.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T083a and T083b integrated and passing differential checks.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T083-report.md` with exact `## Files changed`.

## Out of scope
- Backend code generation (handled in T084).

## Notes
- `model: opus`: Porting the interpreter and optimizer requires semantic precision (model policy).
- Group integration task for T083a and T083b per ADR-0005 §8 and SPEC-20 §4.7.
- Exact differential artefact: interpreter run results & `inspect --emit=mir-opt`.
- Harness entry: `tests/selfhost/interp_opt`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 15:12:25 started (attempt 1) T083-impl
- 2026-10-19 03:16:37 accepted by QA -> done

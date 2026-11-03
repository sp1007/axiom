---
id: T614
title: E15.4 — Interprocedural call-site/constant/closure specialization, devirtualization & tail-call optimization
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T064]
priority: 108
status: todo
attempts: 0
paths: [compiler/opt/ipa, compiler/opt/devirt, tests/run/opt_ipa_devirt]
spec: [spec/SPEC-73-inlining-specialization-devirt.md, 0131, tasks/0400, tasks/0401, tasks/0551]
covers: [REQ-OPT-087, REQ-OPT-088, REQ-OPT-089, REQ-OPT-090, REQ-OPT-091, REQ-OPT-092, REQ-OPT-093, REQ-OPT-094, REQ-OPT-095, REQ-OPT-096, REQ-OPT-097, REQ-OPT-098, REQ-OPT-099, REQ-OPT-100, REQ-OPT-101, REQ-OPT-102, REQ-OPT-103, REQ-OPT-104, REQ-OPT-105, REQ-OPT-106, REQ-OPT-107]
---
# T614 — E15.4 — Interprocedural call-site/constant/closure specialization, devirtualization & tail-call optimization

## Goal
Implement interprocedural constant/closure call-site specialization, proven concrete-target devirtualization of `dyn Trait` and indirect calls, and tail-call / tail-recursion optimization in `compiler/opt/ipa` and `compiler/opt/devirt` per `spec/SPEC-73-inlining-specialization-devirt.md`.

## Scope
- Implement call-site specialization (`compiler/opt/ipa`) cloning and specializing hot functions for constant scalar/aggregate arguments and known closure types (`REQ-OPT-087..102`, `tasks/0551`), bounded by compile-time and code-size budgets and assigning canonical specialized symbol identities.
- Implement devirtualization (`compiler/opt/devirt`) converting `dyn Trait` virtual calls and indirect function-pointer calls into direct calls (or guarded dispatch for proven finite target sets) whenever value/type propagation proves the concrete receiver type (`REQ-OPT-103..107`), feeding newly direct calls back into the inliner.
- Implement tail-recursion loop lowering and ABI-compatible sibling tail-call optimization (`@tailcall`, `0131 §28`), verifying that no live `Drop` glue or stack-borrowed capability spans the tail call.

## Acceptance
- [ ] Differential run and dump tests in `tests/run/opt_ipa_devirt` verify constant/closure specialization, `dyn Trait` devirtualization into inlined direct calls, retention of dynamic dispatch when target identity is unknown, and stack-bounded tail-recursion elimination across `--interp` and native `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T614-report.md` with exact `## Files changed`.

## Out of scope
- Whole-program link-time optimization across separate object archives (`E15.6`, `T620`–`T623`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T614/build` and `python tools/axtest.py --compiler build-snap-T614/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:41:00 created by T215 (P15 phase planning)

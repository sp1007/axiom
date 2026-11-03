---
id: T564
title: E14.3 — Iterator state-machine integration, for-in generator loops & lazy std.iter combinators
phase: P14-comptime-2-0-reflection-genera
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T563]
priority: 184
status: todo
attempts: 0
paths: [std/iter, compiler/lowering, tests/run/iter_gen]
spec: [spec/SPEC-62-generators.md, tasks/0512]
covers: [REQ-CORE-3019, REQ-CORE-3020, REQ-CORE-3021, REQ-CORE-3022, REQ-CORE-3023, REQ-CORE-3024, REQ-CORE-3025]
---
# T564 — E14.3 — Iterator state-machine integration, for-in generator loops & lazy std.iter combinators

## Goal
Integrate generator state machines seamlessly with `for x in gen(...)` loops and `std.iter` lazy iterator adapters (`map`, `filter`, `take`, `skip`, `zip`, `chain`, `enumerate`, `flatten`, `fold`, `collect`) without heap allocation.

## Scope
- Wire `for pattern in expr` lowering in `compiler/lowering` and `std/iter` so any `gen fn` state machine or `IntoIterator` value iterates directly via `next(mut_view(it))` and runs deterministic `Drop` cleanup on `break`, `return`, or loop completion.
- Implement and compose lazy generator-backed and struct-backed adapters in `std/iter`, including nested `yield` delegation (`for item in inner { yield item }`) and comptime generator evaluation (`AGEN-127..128, 140`).

## Acceptance
- [ ] Differential (`--interp` and native) tests in `tests/run/iter_gen` verify `for x in gen_fn(...)` loops, early `break` cleanup, nested generator delegation, comptime generator folding, and `std.iter` adapter chains (`map`/`filter`/`take`/`zip`/`chain`/`enumerate`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T564-report.md` with exact `## Files changed`.

## Out of scope
- E14.3 conformance suite (`T565`) and `dyn Trait` (`E14.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T564/build` and `python tools/axtest.py --compiler build-snap-T564/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:22:30 created by T214 (P14 phase planning)

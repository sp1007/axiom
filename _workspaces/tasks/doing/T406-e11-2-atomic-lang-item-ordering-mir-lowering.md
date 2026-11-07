---
id: T406
title: E11.2 — Atomic<T> lang item, ordering validation & MIR lowering
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T405, T089]
priority: 127
status: doing
attempts: 1
paths: [compiler/mir, std/sync/atomic.ax, tests/mir/atomics, tests/ui/concurrency/atomics]
locks: [compiler/types/typeck.ax, compiler/verify/verifier.ax, compiler/opt/const_fold.ax, compiler/opt/dce.ax, compiler/diag/code.ax, compiler/diag/format.ax, std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-31-atomics.md, 0092, 0128, 0161, 0208, tasks/0328, tasks/0515]
covers: [REQ-CONC-014, REQ-CONC-051, REQ-CONC-052, REQ-CONC-053, REQ-CONC-056, REQ-CONC-057, REQ-CONC-058, REQ-CONC-061, REQ-CONC-062, REQ-CONC-063, REQ-CONC-064, REQ-CONC-069, REQ-CONC-091, REQ-CONC-092, REQ-ASY-061, REQ-ASY-062, REQ-ATM-003, REQ-ATM-004, REQ-ATM-005, REQ-ATM-009, REQ-ATM-011, REQ-ATM-016, REQ-ATM-017, REQ-ATM-020, REQ-ATM-022, REQ-ATM-023, REQ-ATM-024, REQ-ATM-025, REQ-ATM-027, REQ-CONC-098, REQ-CONC-108, REQ-CONC-118, REQ-CONC-121, REQ-CONC-133, REQ-CONC-142, REQ-CONC-173, REQ-CONC-175, REQ-CONC-177, REQ-CONC-201, REQ-ASY-166]
started: 2026-11-07 19:30:36
agent: T406-impl
---
# T406 — E11.2 — Atomic<T> lang item, ordering validation & MIR lowering

## Goal
Implement `std/sync/atomic.ax` (`Atomic<T>`, `Ordering`, `fence`, `compiler_fence`) and lower atomic operations to dedicated MIR `Atomic` statements (`AXS-EXT-043`) with compile-time ordering, width, alignment, and capability validation.

## Scope
- Create `std/sync/atomic.ax` defining `Ordering` (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`), `Atomic<T>` (`!Copy`, `Send + Share` where `T: Send`), `fence`, `compiler_fence`, `spin_loop_hint`, and `is_lock_free<T>()`.
- Wire the `Atomic` lang item and atomic intrinsics in `compiler/types/typeck.ax` and `compiler/mir/builder.ax` so calls lower to MIR `Atomic` statements (`Load`, `Store`, `Rmw`, `CmpXchg`, `Fence`) rather than ordinary loads/stores (`0161 §30`).
- Validate in `compiler/types/typeck.ax` and `compiler/verify/verifier.ax` that `T` is a supported 1/2/4/8-byte integer, `bool`, or raw pointer with natural alignment, reject taking `mut_view<T>` of `Atomic<T>` inner storage, and reject invalid memory orderings (e.g. `Release`/`AcqRel` on `load` or CAS failure ordering, `Acquire`/`AcqRel` on `store`).
- Ensure `compiler/opt/{const_fold,dce}.ax` never folds, reorders, or weakens `Atomic` statements (`REQ-ATM-009, 011, 025`).

## Acceptance
- [ ] `tests/ui/concurrency/atomics/*.ax` verifies compile-time errors for unsupported `Atomic<T>` element types, invalid orderings on `load`/`store`/`compare_exchange`/`fence`, and attempted `mut_view` borrow of `Atomic<T>`.
- [ ] `tests/mir/atomics/*.ax` (`inspect --emit=mir` and `--emit=mir-opt`) verifies that atomic ops lower to explicit MIR `Atomic` statements and preserve orderings at `-O1`.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T406` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T406-report.md` with exact `## Files changed`.

## Out of scope
- LIR/x86-64 native codegen (`T407`) and oracle multi-schedule execution (`T408`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T406/build` and `python tools/axtest.py --compiler build-snap-T406/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-07 19:30:36 started (attempt 1) T406-impl

---
id: T402
title: E11.1 — Compile-time data-race & shared-mutable-state verifier
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T401]
priority: 123
status: done
attempts: 1
paths: [compiler/own, compiler/verify/verifier.ax, compiler/verify/mod.ax, tests/ui/concurrency/data_race, tests/run/concurrency/disjoint]
locks: [compiler/mir/mir.ax, compiler/own_mir_verify/session.ax, compiler/diag/code.ax, compiler/diag/format.ax, tests/selfhost]
spec: [spec/SPEC-30-concurrency.md, 0079, 0091, 0105, 0126, 0136, tasks/0298, tasks/0488, tasks/0685]
covers: [REQ-CONC-004, REQ-CONC-012, REQ-CONC-065, REQ-CONC-066, REQ-CONC-084, REQ-CONC-111, REQ-CONC-129, REQ-CONC-154, REQ-CONC-157, REQ-CONC-165, REQ-CONC-167, REQ-CONC-168, REQ-CONC-169, REQ-CONC-170, REQ-CONC-171, REQ-CONC-194, REQ-CONC-195, REQ-CONC-196]
started: 2026-11-07 15:08:48
finished: 2026-11-07 19:29:27
---
# T402 — E11.1 — Compile-time data-race & shared-mutable-state verifier

## Goal
Extend the ownership, capability, and MIR verification passes in `axiomc` so that any unsynchronized concurrent access to ordinary memory is rejected at compile time with clear conflict diagnostics.

## Scope
- Extend `compiler/own/cap.ax`, `compiler/own/unsafe.ax`, and `compiler/verify/verifier.ax` to verify concurrent access regions across execution contexts (`tasks/0488`).
- Permit concurrent `READ/READ` sharing across contexts via `view<T>` only when `T: Share`; reject `view<T>` sharing across threads when `T: !Share` (`0126 §50, §59`).
- Reject unsynchronized `READ/WRITE` and `WRITE/WRITE` conflicts on overlapping places across concurrent execution contexts (`ACONCUR-150..152`), never treating `UNKNOWN` region overlap as `DISJOINT`.
- Permit concurrent mutable borrows (`mut_view`) of provably disjoint struct fields (`p.a` vs `p.b`) and disjoint slice sub-ranges (`0126 §48`, `ACONCUR-153, 176`).
- Reject access to mutable global ordinary memory outside `unsafe` unless wrapped in a synchronization type (`Mutex`, `RwLock`, `Atomic`), and ensure `unsafe` blocks do not disable concurrency verification once a safe capability is re-established (`ACONCUR-177..178`).
- Emit `AX_CONC_*` diagnostics exposing conflicting places, regions, execution domains, and missing synchronization contracts (`ACONCUR-197`).

## Acceptance
- [ ] `tests/ui/concurrency/data_race/*.ax` tests compile-time rejection of: concurrent `mut_view` + `view` to the same place, concurrent `mut_view` to overlapping/unknown indices, cross-thread `view<T>` where `T: !Share`, unsynchronized mutable static access, and `Arc<T>` mutation without a lock.
- [ ] `tests/run/concurrency/disjoint/*.ax` (`modes: interp native`) verifies concurrent read sharing of `Share` data and disjoint field/subslice `mut_view` operations.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T402` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T402-report.md` with exact `## Files changed`.

## Out of scope
- Runtime thread sanitizer instrumentation (Phase 17 `E17.6`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T402/build` and `python tools/axtest.py --compiler build-snap-T402/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-07 15:08:48 started (attempt 1) T402-impl
- 2026-11-07 19:29:27 accepted by QA -> done

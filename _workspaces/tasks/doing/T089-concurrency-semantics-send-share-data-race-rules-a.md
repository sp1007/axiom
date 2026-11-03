---
id: T089
title: E11.1 — Send and Share auto-trait derivation & negative impl solver
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T211, T400]
priority: 121
status: doing
attempts: 1
paths: [compiler/traits, std/core/marker.ax, tests/ui/concurrency/send_share, tests/run/concurrency/send_share, tests/selfhost/traits]
locks: [compiler/hir/hir.ax, compiler/hir/lower.ax, compiler/types/typeck.ax, compiler/diag/code.ax, std/core/prelude.ax]
spec: [spec/SPEC-30-concurrency.md, 0091, 0092, 0079, 0126, tasks/0276, tasks/0298, tasks/0488, 0208]
covers: [REQ-CONC-218, REQ-CONC-219]
started: 2026-11-03 08:23:12
agent: T089-impl
---
# T089 — E11.1 — Send and Share auto-trait derivation & negative impl solver

## Goal
Implement the `Send` and `Share` auto-traits in `std/core/marker.ax` and the `axiomc` trait solver (`compiler/traits/solver.ax`) per `spec/SPEC-30-concurrency.md`, establishing the type-system foundation for compile-time data-race freedom (`E11.1`).

## Scope
- Define `Send` and `Share` lang-item marker traits in `std/core/marker.ax` and re-export them in `std/core/prelude.ax`.
- Implement `is_auto` and `unsafe trait` / `unsafe impl` handling in `compiler/hir/lower.ax`, `compiler/types/typeck.ax`, and `compiler/traits/solver.ax` (`AXS-EXT-023`, `AXS-EXT-031`).
- Derive `Send` and `Share` structurally for structs, enums, tuples, arrays, and slices when all constituent fields satisfy the trait; keep `Send` and `Share` independent (`Send != Share`).
- Enforce built-in rules: primitives (`bool`, `char`, integers, `Str`) are `Send + Share`; raw pointers (`*const T`, `*mut T`) are `!Send` and `!Share` by default; `view<T>` is `Send + Share` iff `T: Share`; `mut_view<T>` is `Send` iff `T: Send` and is `!Share`.
- Require `unsafe impl Send for T` / `unsafe impl Share for T` when overriding default derivation for types containing raw pointers or synchronization primitives, and support negative impl markers (`!Send`, `!Share`).

## Acceptance
- [ ] `tests/ui/concurrency/send_share/*.ax` verifies rejection of `!Send` and `!Share` types (raw pointers, negative-impl structs, `view<T>` where `T: !Share`, `mut_view<T>` across `Share` bounds) and rejection of safe (non-`unsafe`) manual `impl Send`/`impl Share`.
- [ ] `tests/run/concurrency/send_share/*.ax` (`modes: interp native`) verifies structural auto-derivation of `Send` and `Share` across nested generic structs, enums, tuples, and arrays.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T089` under `axiomc2.exe`; build warning-free; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T089-report.md` with exact `## Files changed`.

## Out of scope
- Closure/spawn capture checks (`T401`), concurrent place conflict verifier (`T402`), and `Atomic<T>` lowering (`T406`–`T408`).

## Notes
- Roadmap epic E11.1. Implemented in `compiler/` (Axiom) / `std/` — `axiom0` is frozen after T087 (ROADMAP R3).
- Refined by T211 as the first implementation slice of E11.1 after `T400` (`SPEC-30`), followed by `T401`–`T404`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:55 covers += REQ-CONC-218, REQ-CONC-219 (metadata only)
- 2026-11-03 00:10:00 refined scope, paths, locks, and dependencies in T211 (P11 phase planning)
- 2026-11-03 08:23:12 started (attempt 1) T089-impl

---
id: T501
title: E13.1 — Unsafe checking, pointer provenance & REQ-OWNER-008 address intrinsics (fn_addr, static_addr, @addr)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T500]
priority: 151
status: todo
attempts: 0
paths: [compiler/hir, compiler/types, compiler/mir, tests/ui/unsafe, tests/mir/unsafe]
locks: [compiler/syntax, compiler/own, compiler/verify, compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0071, 0044, tasks/0339, tasks/0282]
covers: [REQ-OWNER-008, REQ-CAP-003, REQ-CAP-013, REQ-CAP-015, REQ-CAP-018, REQ-CAP-025, REQ-CAP-026, REQ-CAP-027, REQ-CAP-031, REQ-CAP-032, REQ-CAP-033, REQ-CAP-034, REQ-CAP-040, REQ-CAP-046, REQ-CAP-047, REQ-CAP-049, REQ-CAP-051, REQ-CAP-056, REQ-CAP-061, REQ-CAP-062, REQ-CAP-065, REQ-CAP-067, REQ-CAP-069, REQ-CAP-070, REQ-CAP-073, REQ-CAP-083, REQ-CAP-085, REQ-CAP-086, REQ-CAP-093, REQ-CAP-102, REQ-CAP-105, REQ-CAP-107, REQ-CAP-109, REQ-CAP-118, REQ-CAP-122, REQ-CAP-125, REQ-CAP-127, REQ-CAP-129, REQ-CAP-144, REQ-TYP-349, REQ-CAP-146, REQ-CAP-148, REQ-CAP-149, REQ-CAP-150, REQ-CAP-151]
---
# T501 — E13.1 — Unsafe checking, pointer provenance & REQ-OWNER-008 address intrinsics (fn_addr, static_addr, @addr)

## Goal
Implement full `unsafe` block/fn/trait/impl checking, raw-pointer-to-view provenance tracking, and `REQ-OWNER-008` address-taking and `@addr(<expr>)` fixed-address placement across HIR, `typeck`, and MIR lowering.

## Scope
- Enforce `unsafe` context checks in `compiler/types` for raw pointer dereferences, `unsafe fn` calls, `unsafe trait` implementations, `extern` calls, and mutable `static mut` accesses (`AX_UNSAFE_*` diagnostics).
- Implement **`REQ-OWNER-008`** intrinsics and casts: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v)` (`*const T`), `address_of_mut(v)` (`*mut T`), `addr_of(v) -> usize`, `address_of(v) as usize`, and function-item / fn-pointer `as usize` casts in `compiler/types` and `compiler/mir`.
- Implement `@addr(<expr>)` (and `@at(<expr>)`) fixed-address placement attribute lowering on `static`, `let`, and `fn` items/bindings, supporting both compile-time constant addresses and dynamic `usize` expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`).
- Lower raw-pointer-to-`view<T>`/`mut_view<T>` conversions in `unsafe` blocks to explicit `MakeView`/`MakeMutView` MIR instructions preserving provenance and capability verification after the `unsafe` boundary.

## Acceptance
- [ ] Positive and negative UI/MIR tests in `tests/ui/unsafe` and `tests/mir/unsafe` verify `unsafe` block/fn/trait enforcement and raw-pointer-to-view provenance tracking.
- [ ] Tests verify `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) as usize`, and `@addr(<expr>)` placement on `static`, `let`, and `fn` (including `let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T501-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T501/build` and `python tools/axtest.py --compiler build-snap-T501/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)

---
id: T526
title: E13.6 — @at / @addr placement & overlay HIR/THIR/MIR lowering, fixed provenance, overlap & layout checks
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T501, T508, T512, T525]
priority: 175
status: todo
attempts: 0
paths: [compiler/hir, compiler/types, compiler/mir, tests/ui/fixed_addr]
spec: [spec/SPEC-55-fixed-address-declarations.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0071, 0044, 0097, tasks/0328]
covers: [REQ-OWNER-008, REQ-OWNER-003, REQ-ABI-055, REQ-ABI-056, REQ-ABI-083, REQ-RES-145, REQ-CAP-140, REQ-CAP-143]
---
# T526 — E13.6 — @at / @addr placement & overlay HIR/THIR/MIR lowering, fixed provenance, overlap & layout checks

## Goal
Implement full `@at(<expr>)` and `@addr(<expr>)` overlay and placement semantics in HIR, `typeck`, capability/ownership analysis, and MIR lowering (`ADR-0001` §1–4 & §7, `REQ-OWNER-003`, `REQ-OWNER-008`).

## Scope
- Lower `@at(<expr>)` and `@addr(<expr>)` on `static`, `static mut`, `let`, `fn`, and `extern fn` to `Placement { kind: Overlay | Place, address, region }` in `compiler/hir` and `compiler/types`, removing the bootstrap `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` rejection in `axiomc`.
- Enforce compile-time checks (`ADR-0001 §3`): `unsafe` on the declaration, defined layout (`@repr(C)` or primitive/array thereof), address alignment >= type alignment (`AX_UNSAFE_AT_MISALIGNED`), intra-module address range overlap detection (`AX_UNSAFE_AT_OVERLAP`), and profile/region validation (`AX_UNSAFE_AT_HOSTED` when outside allowed mapped/dynamic regions).
- Lower `@at`/`@addr` items in `compiler/mir` to `FixedStatic` places with `fixed` provenance (`never moved, never dropped`), automatic `volatile_load`/`volatile_store` lowering on `Volatile<T>`/`Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` fields, and dynamic runtime address expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`).

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/fixed_addr` verify `@at`/`@addr` overlay and placement declarations, alignment errors, overlap errors, layout-unspecified struct rejection, `MmioRO`/`MmioWO` access checks, and `REQ-OWNER-008` address expressions.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T526-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T526/build` and `python tools/axtest.py --compiler build-snap-T526/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:05:00 created by T213 (P13 phase planning)

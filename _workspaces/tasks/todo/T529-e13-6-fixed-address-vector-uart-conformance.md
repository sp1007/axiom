---
id: T529
title: E13.6 — Fixed-address (@at / @addr) vector table, UART MMIO & REQ-OWNER-003/008 round-trip conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T526, T527, T528]
priority: 178
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_6_fixed_addr]
spec: [spec/SPEC-55-fixed-address-declarations.md, spec/decisions/ADR-0001-fixed-address-declarations.md]
covers: [REQ-OWNER-008, REQ-OWNER-003]
---
# T529 — E13.6 — Fixed-address (@at / @addr) vector table, UART MMIO & REQ-OWNER-003/008 round-trip conformance suite

## Goal
Certify the E13.6 exit criterion ("a freestanding test image with an `@at` vector table and UART register block runs under the oracle with a device model, and native images place every `@at` object at its address, verified via `addr_of` / `address_of` / `fn_addr` / `static_addr`").

## Scope
- Build the canonical freestanding vector-table + UART MMIO + ROM function conformance suite in `tests/conformance/p13/e13_6_fixed_addr` exercising `@at` and `@addr` overlays and placements for `static`, `static mut`, `let`, arrays, `@repr(C)` structs with `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` fields, `fn`, and `extern "C" fn`.
- Verify **`REQ-OWNER-003`** and **`REQ-OWNER-008`** in both `--interp` and native execution: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `addr_of(v) -> usize`, `address_of(v) as usize`, dynamic expression placement (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`), and round-trip assertions (`fn_addr(isr) == 0x2000_0000usize`).

## Acceptance
- [ ] All positive and negative conformance tests in `tests/conformance/p13/e13_6_fixed_addr` pass in `--interp` and native execution with `0 WEAK-NATIVE`, plus `objdump` verification of placed section VMAs and absolute symbols.
- [ ] Report `_workspaces/reports/T529-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T529/build` and `python tools/axtest.py --compiler build-snap-T529/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:05:00 created by T213 (P13 phase planning)

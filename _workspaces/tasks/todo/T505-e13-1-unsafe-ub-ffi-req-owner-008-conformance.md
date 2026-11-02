---
id: T505
title: E13.1 — Unsafe, UB, provenance, FFI & REQ-OWNER-008 address-placement conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T501, T502, T503, T504]
priority: 154
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_1_unsafe_ffi_addr]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0001-fixed-address-declarations.md, spec/decisions/ADR-0034-oracle-independence.md]
covers: [REQ-OWNER-008, REQ-FFI-014, REQ-FFI-017, REQ-FFI-030, REQ-FFI-033, REQ-FFI-040, REQ-FFI-055, REQ-FFI-057, REQ-FFI-064, REQ-FFI-067, REQ-FFI-068, REQ-FFI-076, REQ-FFI-077, REQ-FFI-079, REQ-FFI-084, REQ-FFI-086, REQ-FFI-089, REQ-FFI-092, REQ-FFI-100, REQ-FFI-109, REQ-FFI-111, REQ-FFI-112, REQ-FFI-114, REQ-FFI-116]
---
# T505 — E13.1 — Unsafe, UB, provenance, FFI & REQ-OWNER-008 address-placement conformance suite

## Goal
Certify E13.1 exit criteria with an end-to-end conformance suite covering `unsafe` rules, pointer provenance, FFI/ABI boundaries, and `REQ-OWNER-008` address introspection and `@addr(<expr>)` placement.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p13/e13_1_unsafe_ffi_addr` covering `unsafe` blocks/fns/traits, raw pointer provenance and aliasing rules, raw-pointer-to-`view`/`mut_view` boundaries, and `@repr(C)`/`@repr(transparent)` FFI interop.
- Create dedicated differential (`--interp` and native) conformance tests for **`REQ-OWNER-008`**: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) as usize`, and `@addr(<expr>)` fixed-address placement on `static`, `let`, and `fn`, explicitly testing dynamic expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`) and round-trip assertions (`fn_addr(isr) == 0x2000_0000usize`).

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p13/e13_1_unsafe_ffi_addr` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] `REQ-OWNER-008` round-trip assertions (`fn_addr(isr) == 0x2000_0000usize`, `static_addr`, `address_of(v) as usize`, and dynamic `@addr(base + 0x100)` on `static`, `let`, and `fn`) pass identically in oracle and native.
- [ ] Report `_workspaces/reports/T505-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T505/build` and `python tools/axtest.py --compiler build-snap-T505/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)

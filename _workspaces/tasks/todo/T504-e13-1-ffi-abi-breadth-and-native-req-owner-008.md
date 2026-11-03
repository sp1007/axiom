---
id: T504
title: E13.1 — FFI & C ABI breadth: @repr(C)/@repr(transparent), C callbacks & native REQ-OWNER-008 codegen
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T501, T503]
priority: 153
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, tests/run/ffi, tests/run/unsafe/addr_native, tests/selfhost]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0001-fixed-address-declarations.md, spec/decisions/ADR-0034-oracle-independence.md, 0104, 0181]
covers: [REQ-OWNER-008, REQ-ABI-011, REQ-ABI-018, REQ-ABI-019, REQ-ABI-024, REQ-FFI-007, REQ-ABI-039, REQ-FFI-011, REQ-FFI-012, REQ-FFI-016, REQ-ABI-049, REQ-ABI-053, REQ-ABI-057, REQ-ABI-059, REQ-ABI-060, REQ-FFI-021, REQ-FFI-022, REQ-ABI-067, REQ-FFI-025, REQ-FFI-026, REQ-FFI-028, REQ-FFI-032, REQ-FFI-034, REQ-FFI-035, REQ-FFI-036, REQ-FFI-037, REQ-FFI-039, REQ-FFI-046, REQ-FFI-047, REQ-FFI-048, REQ-FFI-049, REQ-FFI-050, REQ-FFI-051, REQ-FFI-052, REQ-FFI-053, REQ-FFI-054, REQ-FFI-056, REQ-FFI-059, REQ-FFI-060, REQ-FFI-062, REQ-FFI-063, REQ-FFI-065, REQ-FFI-069, REQ-FFI-070, REQ-FFI-071, REQ-FFI-072, REQ-FFI-073, REQ-FFI-074, REQ-FFI-075, REQ-FFI-081, REQ-FFI-082, REQ-FFI-083, REQ-FFI-087, REQ-FFI-090, REQ-FFI-091, REQ-FFI-095, REQ-FFI-096, REQ-FFI-101, REQ-FFI-102, REQ-FFI-103, REQ-FFI-104, REQ-FFI-105, REQ-FFI-106, REQ-FFI-107, REQ-FFI-108, REQ-FFI-110, REQ-FFI-113, REQ-FFI-115, REQ-RES-133, REQ-RES-134, REQ-RES-159, REQ-RES-167, REQ-RES-168, REQ-RES-169, REQ-ABI-091, REQ-FFI-118, REQ-FFI-120, REQ-FFI-122, REQ-FFI-123, REQ-ABI-097, REQ-ABI-099, REQ-ABI-101, REQ-FFI-126]
---
# T504 — E13.1 — FFI & C ABI breadth: @repr(C)/@repr(transparent), C callbacks & native REQ-OWNER-008 codegen

## Goal
Implement full FFI/ABI layout and calling convention lowering (`@repr(C)`, `@repr(transparent)`, `@abi(stable)`, C callbacks, opaque foreign types) and native x86-64 codegen for `REQ-OWNER-008` (`fn_addr`, `static_addr`, `address_of(v) as usize`, `@addr(<expr>)`).

## Scope
- Enforce `@repr(C)`, `@repr(transparent)`, `@abi(stable)`, and opaque `extern type` layout and ABI rules in LIR and x86-64 lowering, rejecting non-FFI-safe types (closures, `dyn`, layout-unspecified structs) on `extern "C"` signatures unless explicitly wrapped.
- Support `extern "C" fn` pointers as first-class FFI callbacks passed to and invoked from C code, preserving callee-saved registers and Windows x64 shadow space.
- Implement native x86-64 LIR/isel/object lowering for **`REQ-OWNER-008`**: `fn_addr(f) -> usize` (RIP-relative `LEA` or absolute target address), `static_addr(s) -> usize`, `address_of(v) as usize`, and `@addr(<expr>)` fixed-address placement for `static`, `let`, and `fn` (including dynamic runtime address binding `let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;` and round-trip `fn_addr(isr) == 0x2000_0000usize`).

## Acceptance
- [ ] All tests in `tests/ffi/win64_abi_oracle` (`T503`), `tests/run/ffi`, and `tests/run/unsafe/addr_native` pass natively under `axiomc2.exe`.
- [ ] Native execution verifies `fn_addr`, `static_addr`, `address_of(v) as usize`, and `@addr(<expr>)` for `static`, `let`, and `fn` (both constant addresses and dynamic `base + 0x100` expressions).
- [ ] Report `_workspaces/reports/T504-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T504/build` and `python tools/axtest.py --compiler build-snap-T504/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)

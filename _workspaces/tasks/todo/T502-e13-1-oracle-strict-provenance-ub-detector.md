---
id: T502
title: E13.1 — Oracle strict-provenance & UB detector (use-after-free, unaligned, uninit, REQ-OWNER-008 round-trip)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T501]
priority: 152
status: todo
attempts: 0
paths: [compiler/interp, tests/run/unsafe/oracle_ub, tests/selfhost]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, 0071, 0044, tasks/0339]
covers: [REQ-OWNER-008, REQ-CAP-001, REQ-CAP-002, REQ-CAP-005, REQ-CAP-007, REQ-CAP-019, REQ-CAP-037, REQ-CAP-038, REQ-CAP-041, REQ-CAP-048, REQ-FFI-027, REQ-FFI-038, REQ-FFI-044, REQ-FFI-045, REQ-CAP-059, REQ-CAP-071, REQ-CAP-078, REQ-CAP-084, REQ-CAP-087, REQ-CAP-088, REQ-CAP-091, REQ-CAP-095, REQ-CAP-098, REQ-CAP-103, REQ-CAP-111, REQ-FFI-085, REQ-FFI-088, REQ-CAP-124, REQ-CAP-126, REQ-CAP-133, REQ-MIR-142, REQ-CAP-145, REQ-FFI-128]
---
# T502 — E13.1 — Oracle strict-provenance & UB detector (use-after-free, unaligned, uninit, REQ-OWNER-008 round-trip)

## Goal
Extend the MIR oracle (`--interp`) with strict pointer provenance tags, deterministic UB detection, and `REQ-OWNER-008` fixed/dynamic address table evaluation.

## Scope
- Tag every oracle allocation and pointer value in `compiler/interp` with an allocation ID, bounds, alignment, mutability permission, and per-byte initialization state.
- Detect and deterministically diagnose UB in `--interp`: dereferencing dangling/freed pointers, out-of-bounds pointer arithmetic or loads/stores, unaligned accesses on non-packed types, reading uninitialized memory, and violating `mut_view<T>` exclusivity through raw pointers.
- Implement oracle evaluation for **`REQ-OWNER-008`**: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) as usize`, and `@addr(<expr>)` fixed-address placement for `static`, `let`, and `fn`, including dynamic expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`) and round-trip assertions (`fn_addr(isr) == 0x2000_0000usize`).

## Acceptance
- [ ] Oracle UB tests in `tests/run/unsafe/oracle_ub` catch use-after-free, out-of-bounds raw pointer deref, unaligned deref, uninitialized read, and provenance forgery with deterministic diagnostics.
- [ ] Oracle round-trip tests pass for `fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`, and `address_of(v) as usize` on `@addr(<expr>)` `static`, `let`, and `fn` declarations.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T502-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T502/build` and `python tools/axtest.py --compiler build-snap-T502/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)

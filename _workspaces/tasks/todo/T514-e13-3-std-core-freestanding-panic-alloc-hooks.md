---
id: T514
title: E13.3 — Freestanding std.core subset, explicit panic/alloc/DMA hooks & zero-OS runtime layer
phase: P13-low-level-systems-unsafe-frees
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T512, T513]
priority: 163
status: todo
attempts: 0
paths: [std/core, std/alloc, tests/std/freestanding_core]
spec: [spec/SPEC-52-freestanding-runtime-composition.md, 0143, 0097, tasks/0358, tasks/0359]
covers: [REQ-FFI-006, REQ-FFI-009, REQ-FFI-020, REQ-FFI-024, REQ-FFI-058, REQ-ABI-078, REQ-FFI-080, REQ-RES-170, REQ-FFI-121]
---
# T514 — E13.3 — Freestanding std.core subset, explicit panic/alloc/DMA hooks & zero-OS runtime layer

## Goal
Ensure `std/core` (and optional `std/alloc` with a user-supplied allocator) compiles and runs cleanly under `--profile freestanding` without any OS or `std.os`/`std.io` dependency, including explicit foreign-allocator and DMA buffer ownership wrappers.

## Scope
- Audit and modularize `std/core` (`Option`, `Result`, slices, views, iterators, `fmt` into fixed byte buffers, `cmp`, `hash`, `num`, `mem`, `ptr`) so zero symbols from `std/os` or `kernel32` are referenced in `--profile freestanding`.
- Provide pluggable `@panic_handler` (`PanicInfo`) and optional `@global_allocator` (`Allocator` trait) hooks in `std/core/panic.ax` and `std/alloc`.
- Provide explicit foreign-allocation domain (`ForeignBox<T, A>`) and DMA pinned-buffer ownership guards (`DmaBuffer<T>` preventing CPU `mut_view` access while a device transfer token is active per `REQ-CAP-140`, `REQ-CAP-143`).

## Acceptance
- [ ] Tests in `tests/std/freestanding_core` compile and run `std.core` + custom static arena `std.alloc` under `--profile freestanding` in both `--interp` and native modes with zero OS imports.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T514-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T514/build` and `python tools/axtest.py --compiler build-snap-T514/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:02:00 created by T213 (P13 phase planning)

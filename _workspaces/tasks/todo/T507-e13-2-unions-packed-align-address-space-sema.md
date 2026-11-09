---
id: T507
title: E13.2 — Unions, @repr(packed)/@align(N), unaligned field diagnostics & address-space type checking
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T506]
priority: 156
status: todo
attempts: 0
paths: [compiler/syntax, compiler/hir, compiler/types, tests/ui/layout]
locks: [compiler/lex, compiler/resolve, compiler/own, compiler/mir, compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-51-raw-memory-volatile-mmio-layout.md, 0067, 0072, tasks/0328]
covers: [REQ-ABI-036, REQ-ABI-041, REQ-FFI-097, REQ-FFI-098, REQ-RES-135]
---
# T507 — E13.2 — Unions, @repr(packed)/@align(N), unaligned field diagnostics & address-space type checking

## Goal
Implement untagged `union` types, `@repr(packed)` / `@align(N)` layout computation, unaligned packed-field capability/pointer diagnostics, and address-space qualifier checking in the frontend and semantic analyzer.

## Scope
- Parse and lower `union` declarations in `compiler/parser`, `compiler/hir`, and `compiler/types`: compute size = max field size rounded to alignment, enforce `Copy` / `ManuallyDrop<T>` field constraints, and require `unsafe` for reading union fields.
- Implement `@repr(packed)`, `@repr(packed(N))`, and `@align(N)` (power-of-two validation) in layout calculation, rejecting conflicting `@repr(packed)` + `@align(N)` attributes on the same type, and enforce deterministic zero-initialization of alignment padding bytes in `@repr(C)` / `@repr(packed)` struct constructors (ASLR infoleak defense).
- Reject taking `view<T>`, `mut_view<T>`, or aligned `*const T`/`*mut T` to an unaligned field of a `@repr(packed)` struct (`AX_TYPE_UNALIGNED_PACKED_REF`), while permitting by-value copy reads/writes and `read_unaligned`/`write_unaligned`.
- Check explicit pointer address-space qualifiers so device/physical address-space pointers cannot implicitly coerce to default host pointers.

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/layout` cover `union` declarations, `unsafe` union field reads, `@repr(packed)` and `@align(N)` layout sizes/offsets, and `AX_TYPE_UNALIGNED_PACKED_REF` diagnostics.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T507-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T507/build` and `python tools/axtest.py --compiler build-snap-T507/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:01:00 created by T213 (P13 phase planning)

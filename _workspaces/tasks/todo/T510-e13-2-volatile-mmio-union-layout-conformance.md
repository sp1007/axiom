---
id: T510
title: E13.2 — Raw memory, volatile, MMIO, union & layout-control conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T507, T508, T509]
priority: 159
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_2_volatile_mmio_layout]
spec: [spec/SPEC-51-raw-memory-volatile-mmio-layout.md, 0067, 0072, tasks/0328, tasks/0515]
covers: [REQ-ABI-012, REQ-ABI-044, REQ-FFI-013, REQ-ABI-052, REQ-FFI-018, REQ-ABI-061, REQ-ABI-064, REQ-ABI-065, REQ-FFI-029, REQ-FFI-043, REQ-FFI-078, REQ-RES-163, REQ-ABI-093, REQ-ABI-098, REQ-ABI-100, REQ-ABI-103]
---
# T510 — E13.2 — Raw memory, volatile, MMIO, union & layout-control conformance suite

## Goal
Certify E13.2 exit criteria with a conformance suite covering volatile operations, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>`, untagged `union` types, `@repr(packed)`/`@align(N)`, `MaybeUninit<T>`, and `bitcast`.

## Scope
- Write positive and negative conformance tests in `tests/conformance/p13/e13_2_volatile_mmio_layout` verifying volatile access ordering and non-tearing width guarantees, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` read/write restrictions, `union` initialization and `unsafe` field reads, `@repr(packed)` unaligned-view rejection, and `MaybeUninit<T>`/`bitcast` safety rules.
- Verify differential agreement between `--interp` and native execution across all runnable E13.2 tests.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p13/e13_2_volatile_mmio_layout` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T510-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T510/build` and `python tools/axtest.py --compiler build-snap-T510/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:01:00 created by T213 (P13 phase planning)

---
id: T509
title: E13.2 — std.mem.volatile, Mmio<T>/MmioRO<T>/MmioWO<T>, MaybeUninit<T>, bitfields & layout API
phase: P13-low-level-systems-unsafe-frees
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T508]
priority: 158
status: todo
attempts: 0
paths: [std/mem, tests/std/mem_volatile_mmio, tests/selfhost]
spec: [spec/SPEC-51-raw-memory-volatile-mmio-layout.md, spec/decisions/ADR-0001-fixed-address-declarations.md, 0067, 0072, tasks/0328]
covers: [REQ-FFI-031, REQ-RES-137, REQ-RES-160, REQ-RES-161]
---
# T509 — E13.2 — std.mem.volatile, Mmio<T>/MmioRO<T>/MmioWO<T>, MaybeUninit<T>, bitfields & layout API

## Goal
Implement the standard library raw memory, volatile, MMIO register (`Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`), `MaybeUninit<T>`, `ManuallyDrop<T>`, `transmute`/`bitcast`, and layout introspection APIs in `std/mem`.

## Scope
- Implement `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, and `MmioWO<T>` in `std/mem/mmio.ax` with `read`, `write`, `modify`, and bitmask helper methods (`set_bits`, `clear_bits`, `test_bits`), plus direct compiler-lowered field access support (`ADR-0001 §2`).
- Implement `MaybeUninit<T>` (`uninit`, `zeroed`, `new`, `write`, `assume_init`, `as_ptr`, `as_mut_ptr`) and `ManuallyDrop<T>` in `std/mem`.
- Implement size-and-alignment checked `bitcast<From, To>(v: From) -> To`, `size_of<T>()`, `align_of<T>()`, `offset_of(Type, field)`, `read_unaligned`, `write_unaligned`, and `zeroed`.

## Acceptance
- [ ] Unit and differential tests in `tests/std/mem_volatile_mmio` verify `Volatile<T>`, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>`, `MaybeUninit<T>`, `ManuallyDrop<T>`, `bitcast`, and `offset_of` in both `--interp` and native execution.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T509-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T509/build` and `python tools/axtest.py --compiler build-snap-T509/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:01:00 created by T213 (P13 phase planning)

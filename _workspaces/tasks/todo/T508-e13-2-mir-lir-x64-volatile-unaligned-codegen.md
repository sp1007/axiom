---
id: T508
title: E13.2 — MIR/LIR/x64 volatile load/store/fence lowering, non-tearing width guarantees & unaligned codegen
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T507]
priority: 157
status: todo
attempts: 0
paths: [compiler/mir, compiler/lir, compiler/target/x64, tests/lir/volatile, tests/run/volatile]
spec: [spec/SPEC-51-raw-memory-volatile-mmio-layout.md, tasks/0328, tasks/0515]
covers: [REQ-FFI-015, REQ-RES-173]
---
# T508 — E13.2 — MIR/LIR/x64 volatile load/store/fence lowering, non-tearing width guarantees & unaligned codegen

## Goal
Lower volatile memory operations, `Volatile<T>`/`Mmio<T>` field accesses, and unaligned packed field loads/stores through MIR, LIR, `-O1`, and the x86-64 backend with strict non-elision and exact-width instruction selection.

## Scope
- Lower `volatile_load`, `volatile_store`, `volatile_copy`, `compiler_fence`, and `Volatile<T>` / `Mmio<T>` / `MmioRO<T>` / `MmioWO<T>` field projections in `compiler/mir` and `compiler/lir` with side-effect barrier flags so `-O1` never CSEs, dead-stores, or reorders volatile operations.
- Emit exact-width non-tearing x86-64 instructions (`MOV r8/m8`, `MOV r16/m16`, `MOV r32/m32`, `MOV r64/m64`, `MFENCE`/`SFENCE`/`LFENCE`) in `compiler/target/x64` for 1/2/4/8-byte volatile accesses.
- Lower `read_unaligned`, `write_unaligned`, and `@repr(packed)` field loads/stores safely without assuming natural alignment, and emit deterministic zero-fill stores for inter-field and trailing padding bytes in struct initializers.

## Acceptance
- [ ] LIR golden tests in `tests/lir/volatile` verify that consecutive volatile stores/loads to the same address are never eliminated or merged at `-O1` and emit single exact-width `MOV` instructions.
- [ ] Run tests in `tests/run/volatile` verify volatile and unaligned packed struct operations in both `--interp` and native execution.
- [ ] Report `_workspaces/reports/T508-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T508/build` and `python tools/axtest.py --compiler build-snap-T508/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:01:00 created by T213 (P13 phase planning)

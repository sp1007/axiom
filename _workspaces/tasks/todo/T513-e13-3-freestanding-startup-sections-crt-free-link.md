---
id: T513
title: E13.3 — Freestanding startup, static init order, custom section layout & CRT-free native image emission
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T512]
priority: 162
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, compiler/link, tests/link/freestanding, tests/selfhost]
spec: [spec/SPEC-52-freestanding-runtime-composition.md, 0143, 0097, tasks/0370, tasks/0455]
covers: [REQ-ABI-055, REQ-ABI-056, REQ-ABI-083, REQ-RES-145, REQ-CAP-140, REQ-CAP-143]
---
# T513 — E13.3 — Freestanding startup, static init order, custom section layout & CRT-free native image emission

## Goal
Emit CRT-free and `kernel32.dll`-free native binaries in `--profile freestanding`, lowering `@entry`, `@naked`, `@section("...")`, `@used`, and deterministic const-initialized statics through LIR, COFF object emission, and the linker.

## Scope
- Lower `@entry` as the direct PE/image entry point without emitting the hosted startup stub or default `kernel32.dll` import table when `--profile freestanding` is active.
- Lower `@naked` functions without prologue/epilogue stack frame generation and lower `extern "interrupt"` functions with interrupt-frame preservation (`IRETQ`).
- Emit custom named sections for `@section("...")` items and retain `@used` symbols against dead-strip/section GC in `compiler/obj` and `compiler/link`.

## Acceptance
- [ ] Link and objdump tests in `tests/link/freestanding` verify that a `--profile freestanding` executable has zero DLL imports (`objdump -p` shows no import directory), uses the `@entry` symbol as its entry point, places `@section` items in their named COFF sections, and runs natively.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T513-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T513/build` and `python tools/axtest.py --compiler build-snap-T513/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:02:00 created by T213 (P13 phase planning)

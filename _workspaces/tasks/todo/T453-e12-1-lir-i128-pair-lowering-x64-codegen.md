---
id: T453
title: E12.1 — LIR i128 register-pair lowering & x86-64 native codegen (ADC/SBB/MULX/SHLD/SHRD)
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T451, T452, T481]
priority: 143
status: todo
attempts: 0
paths: [compiler/lir, compiler/abi, compiler/target/x64, tests/lir/int128, tests/encode/int128, tests/run/int128_native]
locks: [compiler/backend/session.ax, tests/selfhost, tests/run/int128_interp, tests/opt/int128]
spec: [spec/SPEC-40-integers.md, spec/SPEC-04-core-extensibility.md, 0162, 0179, 0181, tasks/0327]
covers: [REQ-SIMD-027, REQ-SIMD-266, REQ-SIMD-267]
---
# T453 — E12.1 — LIR i128 register-pair lowering & x86-64 native codegen (ADC/SBB/MULX/SHLD/SHRD)

## Goal
Lower `i128`/`u128` and saturating integer operations through LIR (`AXS-EXT-050`) and Windows x64 ABI to verified x86-64 machine instructions (`ADD`/`ADC`, `SUB`/`SBB`, `MUL`/`IMUL`, `SHLD`/`SHRD`, `CMOVcc`, `BSWAP`, `POPCNT`).

## Scope
- Implement LIR `i128` register-pair (`lo: Gpr`, `hi: Gpr`) lowering in `compiler/lir/lir.ax` and `compiler/lir/builder.ax`, and 16-byte integer argument/return ABI lowering in `compiler/abi/win64.ax`.
- Implement x86-64 instruction selection and encoding in `compiler/target/x64/isel.ax` and `compiler/target/x64/encode.ax` for 128-bit checked and wrapping `ADD`+`ADC`, `SUB`+`SBB`, `MUL`/`IMUL` (with high-word overflow checks), 128-bit division/remainder (`udiv128`/`sdiv128` algorithm), `SHLD`/`SHRD` double-precision shifts and rotates, `BSWAP`, `LZCNT`/`TZCNT`/`BSR`/`BSF`, and `POPCNT`.
- Lower `MirBinOp.SatAdd`, `SatSub`, and `SatMul` for 128-bit signed and unsigned integers using overflow/carry flags + `CMOVcc` saturation to `MIN`/`MAX` without branches. The 8..64-bit lowering is delivered by T481 (ADR-0042 §3); keep it green (you may switch it to the branch-free `CMOVcc` form if T481 used another correct expansion).
- Remove `native-after: T453` from every test under `tests/run/int128_interp` and `tests/opt/int128` (T452's tests, now in `locks:`) so their native legs run.

## Acceptance
- [ ] `tests/lir/int128/*.ax` and `tests/encode/int128/*.ax` verify LIR emission and byte-exact x86-64 encoding for `ADC`, `SBB`, `SHLD`, `SHRD`, `BSWAP`, and saturating `CMOVcc` sequences.
- [ ] `tests/run/int128_native/*.ax` passes in both `--interp` and native x86-64 execution (`WEAK-NATIVE 0`) for 128-bit arithmetic, division/remainder, shifts, saturating ops, and Win64 16-byte call boundaries.
- [ ] `tests/run/int128_interp/*` and `tests/opt/int128/*` (no `native-after` left) pass in native and native-O1 with exact output (`WEAK-NATIVE 0`); `tests/run/saturating_native/*` (T481, all widths 8..64) still pass natively, and a 128-bit row is added to them.
- [ ] Every `tests/selfhost/*/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T453` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T453-report.md` with exact `## Files changed`.

## Out of scope
- Standard library wrapper methods and `TryFrom` traits (`T454`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T453/build` and `python tools/axtest.py --compiler build-snap-T453/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-13 axiom-architect (ADR-0042 §3): depends on T452 and T481 (narrow-width native saturation fixed first); removes `native-after: T453` from T452's tests

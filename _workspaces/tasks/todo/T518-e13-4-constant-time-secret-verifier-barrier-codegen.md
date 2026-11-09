---
id: T518
title: E13.4 — Constant-time secret types (@secret / Secret<T>) branch/index/timing-leak verifier & barrier lowering
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T517]
priority: 167
status: todo
attempts: 0
paths: [compiler/mir, compiler/lir, compiler/target/x64, tests/ui/constant_time, tests/lir/constant_time]
spec: [spec/SPEC-53-safety-profiles-capability-security.md, tasks/0467, tasks/0703]
covers: [REQ-ABI-046, REQ-FFI-124, REQ-CAP-141]
---
# T518 — E13.4 — Constant-time secret types (@secret / Secret<T>) branch/index/timing-leak verifier & barrier lowering

## Goal
Implement the MIR/LIR constant-time verifier for `@constant_time` functions and `Secret<T>` values, plus optimization-proof `black_box` and `zeroize` barriers in `-O1` and x86-64 codegen.

## Scope
- Verify `@constant_time` functions and `Secret<T>` taint propagation in `compiler/mir`: reject secret-dependent `if`/`match`/`while` branches, secret-dependent array/slice indexing, and variable-time instructions (`DIV`/`IDIV`/`REM`) on secret operands (`AX_SEC_TIMING_LEAK`).
- Lower constant-time conditional select (`ct_select`) to branchless x86-64 `CMOVcc` / bitwise masks without `-O1` branch re-introduction.
- Lower `zeroize_memory` and `black_box` as volatile optimization barriers in MIR, LIR, and x86-64 so dead-store elimination never removes secret zeroization on `Drop`, and support `std.security.spectre_index` speculative execution barrier lowering.

## Acceptance
- [ ] Negative UI tests in `tests/ui/constant_time` reject secret-dependent branches, secret table indexing, and secret division in `@constant_time` functions.
- [ ] LIR golden tests in `tests/lir/constant_time` verify branchless `CMOVcc` selection and preserved `zeroize_memory` stores under `-O1`.
- [ ] Report `_workspaces/reports/T518-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T518/build` and `python tools/axtest.py --compiler build-snap-T518/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:03:00 created by T213 (P13 phase planning)

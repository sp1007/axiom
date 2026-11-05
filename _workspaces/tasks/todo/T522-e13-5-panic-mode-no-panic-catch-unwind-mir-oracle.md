---
id: T522
title: E13.5 — --panic abort|unwind mode, @no_panic verification, catch_unwind & FFI boundary abort guards
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T521]
priority: 171
status: todo
attempts: 0
paths: [compiler/driver, compiler/types, compiler/mir, compiler/interp, std/panic, tests/ui/panic, tests/run/panic_oracle]
locks: [compiler/hir, compiler/verify, compiler/diag/code.ax, std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-54-panic-unwinding.md, 0229, tasks/0351, tasks/0700]
covers: [REQ-FFI-041, REQ-FFI-093, REQ-ABI-096, REQ-ABI-105]
---
# T522 — E13.5 — --panic abort|unwind mode, @no_panic verification, catch_unwind & FFI boundary abort guards

## Goal
Implement `--panic abort|unwind` configuration, `@no_panic` static call-graph checking, MIR cleanup edge generation, `extern "C"` FFI no-unwind abort guards, and oracle unwinding with `std.panic.catch_unwind`.

## Scope
- Add `--panic abort|unwind` to `compiler/driver` and `axiom.toml` profiles, defaulting `freestanding` to `abort`.
- Implement `@no_panic` verification in `compiler/types`/`compiler/mir` rejecting calls to panicking functions, unchecked indexing/arithmetic, or `panic(...)` inside `@no_panic` functions (`AX_PANIC_FORBIDDEN_IN_NO_PANIC`).
- Lower MIR unwind cleanup edges on fallible calls under `--panic unwind`, inserting mandatory abort landing pads on `extern "C"` entry points (`REQ-ABI-096`, `REQ-ABI-105`) and double-panic guards inside `Drop.drop`.
- Implement stack unwinding, reverse-order `Drop` execution, FFI boundary abort, and `std.panic.catch_unwind` in `compiler/interp` and `std/panic`.

## Acceptance
- [ ] UI tests in `tests/ui/panic` verify `@no_panic` enforcement.
- [ ] Oracle tests in `tests/run/panic_oracle` verify `catch_unwind` recovery, reverse-order `Drop` cleanup across multiple stack frames, double-panic abort, and `extern "C"` boundary abort.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T522-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T522/build` and `python tools/axtest.py --compiler build-snap-T522/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:04:00 created by T213 (P13 phase planning)

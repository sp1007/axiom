---
id: T523
title: E13.5 — Native MIR cleanup landing pads, Windows x64 SEH unwind tables & deterministic drop unwinding
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T522]
priority: 172
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, compiler/link, tests/run/panic_native, tests/selfhost]
spec: [spec/SPEC-54-panic-unwinding.md, 0188, 0229, tasks/0351, tasks/0700]
covers: [REQ-FFI-094, REQ-FFI-004, REQ-FFI-019, REQ-ABI-096]
---
# T523 — E13.5 — Native MIR cleanup landing pads, Windows x64 SEH unwind tables & deterministic drop unwinding

## Goal
Lower MIR cleanup landing pads, `catch_unwind`, and FFI no-unwind abort barriers to native x86-64 code with Windows x64 SEH `.pdata`/`.xdata` unwind metadata so `Drop` destructors run deterministically during native unwinding.

## Scope
- Lower MIR cleanup blocks and unwind edges in `compiler/lir` and `compiler/target/x64` to frame cleanup handlers and `.pdata`/`.xdata` unwind descriptors in `compiler/obj` and `compiler/link`.
- Implement native `std.panic.catch_unwind` recovery and `extern "C"` boundary abort guards so panics inside Axiom callbacks invoked from C abort deterministically rather than unwinding into C frames (`REQ-FFI-004`, `REQ-FFI-019`, `REQ-ABI-096`).
- Ensure `--panic abort` omits cleanup landing pads and emits direct abort calls with minimal code size.

## Acceptance
- [ ] Native tests in `tests/run/panic_native` verify `catch_unwind`, multi-frame `Drop` cleanup order during unwinding, double-panic abort, and `extern "C"` callback panic abort parity with `--interp`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T523-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T523/build` and `python tools/axtest.py --compiler build-snap-T523/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:04:00 created by T213 (P13 phase planning)

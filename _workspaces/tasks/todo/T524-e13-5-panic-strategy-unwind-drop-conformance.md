---
id: T524
title: E13.5 — Panic strategy, drop cleanup across unwind & FFI boundary abort conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T522, T523]
priority: 173
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_5_panic_unwinding]
spec: [spec/SPEC-54-panic-unwinding.md, 0229, tasks/0351, tasks/0700]
covers: [REQ-FFI-127, REQ-FFI-004, REQ-FFI-019, REQ-ABI-096]
---
# T524 — E13.5 — Panic strategy, drop cleanup across unwind & FFI boundary abort conformance suite

## Goal
Certify E13.5 exit criteria with a conformance suite covering `--panic abort` vs `--panic unwind`, deterministic `Drop` cleanup across stack frames, `@no_panic`, and FFI no-unwind abort boundaries.

## Scope
- Write differential (`--interp` and native) conformance tests in `tests/conformance/p13/e13_5_panic_unwinding` covering `--panic abort`, `--panic unwind` with `catch_unwind`, nested struct/slice `Drop` execution across unwinding frames, double-panic abort, `@no_panic` compile-time checks, and C->Axiom callback panic abort.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p13/e13_5_panic_unwinding` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T524-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T524/build` and `python tools/axtest.py --compiler build-snap-T524/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:04:00 created by T213 (P13 phase planning)

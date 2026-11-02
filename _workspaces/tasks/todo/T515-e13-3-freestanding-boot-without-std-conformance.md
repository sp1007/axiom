---
id: T515
title: E13.3 — Freestanding boot-without-std & runtime composition conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T512, T513, T514]
priority: 164
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_3_freestanding_runtime]
spec: [spec/SPEC-52-freestanding-runtime-composition.md, 0143, 0097, tasks/0358, tasks/0359, tasks/0370, tasks/0455]
covers: [REQ-FFI-005, REQ-FFI-008, REQ-FFI-066, REQ-ABI-031, REQ-ABI-102]
---
# T515 — E13.3 — Freestanding boot-without-std & runtime composition conformance suite

## Goal
Certify the E13.3 and P13 exit criterion ("freestanding program boots without std") across `--interp` and native CRT-free execution.

## Scope
- Build end-to-end freestanding test binaries in `tests/conformance/p13/e13_3_freestanding_runtime` that compile with `--profile freestanding`, define `@entry` and `@panic_handler`, format into a ring buffer using `std.core` without OS/heap, exercise custom `@section` placement and `extern "interrupt"` handlers, and exit cleanly.
- Verify negative conformance tests where `--profile freestanding` or `extern "interrupt"` code attempts to use ambient OS I/O, heap allocation, or blocking operations.

## Acceptance
- [ ] All positive and negative tests in `tests/conformance/p13/e13_3_freestanding_runtime` pass in `--interp` and native execution (`0 WEAK-NATIVE`, verified zero DLL imports via `objdump -p`).
- [ ] Report `_workspaces/reports/T515-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T515/build` and `python tools/axtest.py --compiler build-snap-T515/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:02:00 created by T213 (P13 phase planning)

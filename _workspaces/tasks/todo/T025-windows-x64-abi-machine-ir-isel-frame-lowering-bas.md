---
id: T025
title: Windows x64 ABI lowering + machine IR + baseline isel
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T023, T024, T003a]
priority: 42
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/abi, bootstrap/axiom0/src/target/x64/mir, bootstrap/axiom0/src/target/x64/isel, tests/mc/isel, bootstrap/axiom0/src/driver/emit_mi.c]
locks: [bootstrap/axiom0/src/types/types.h, bootstrap/axiom0/src/lir/lir.h]
spec: [0181, 0189, 0180, 0183, 0251, 0253, 0230, 0231, spec/SPEC-04-core-extensibility.md]
started: 2026-10-07 23:09:14
unblocks: 1
---
# T025 — Windows x64 ABI lowering + machine IR + baseline isel

## Goal
Lower LIR to x86-64 machine IR following the MS x64 ABI with a simple stack-slot strategy. Frame lowering, stack probes, the machine-IR verifier and byte emission are T025b (ADR-0003, ADR-0005 §8).

## Scope
- `abi/win64.c` ABI description as data; **ABI lowering as a LIR→LIR pass before isel** (ADR-0003 A2): argument and return locations (registers + stack), hidden return pointer, by-reference copies of large aggregates, shadow space and 16-byte call alignment recorded as frame requirements.
- x64 machine IR; baseline instruction selection for the VS1 set (constants, integer arithmetic without traps, locals in stack slots, `return`) with fixed scratch registers (`BOOTSTRAP-SHORTCUT`, retired by E15.8).
- Emitter `src/driver/emit_mi.c`: `--emit=mi` prints the machine IR before frame lowering.

## Acceptance
- [ ] `mi` golden tests for the VS1 programs (`return 42`, arithmetic, locals).
- [ ] ABI lowering unit tests (`tests/mc/isel/cdriver_abi.c`): locations for 0–6 integer arguments, an 8-byte and a 16-byte aggregate argument, an aggregate return through the hidden pointer (classification only; code generation for calls is T033).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T025-report.md` with exact `## Files changed`.

## Out of scope
- Branches, calls with arguments, checked arithmetic (T033/T037); prologue/epilogue, stack probes, the machine-IR verifier and encoding to bytes (T025b).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-07 23:09:14 started (attempt 1) T025-impl
- 2026-10-07 23:22:56 block: missing aggregate types and layout queries in types.h and missing frame fields in lir.h; need locks
- 2026-10-07 23:23:47 unblocked (cycle 1) 

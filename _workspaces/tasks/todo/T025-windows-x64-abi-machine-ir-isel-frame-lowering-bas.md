---
id: T025
title: Windows x64 ABI + machine IR + isel + frame lowering (baseline)
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T023, T024, T003a]
priority: 42
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/abi, bootstrap/axiom0/src/target/x64/mir, bootstrap/axiom0/src/target/x64/isel, bootstrap/axiom0/src/target/x64/frame, tests/mc]
spec: [0181, 0189, 0180, 0183, 0251, 0253, 0230, 0231, spec/SPEC-04-core-extensibility.md]
---
# T025 — Windows x64 ABI + machine IR + isel + frame lowering (baseline)

## Goal
Lower LIR to encoded x86-64 functions following the MS x64 ABI with a simple stack-slot strategy.

## Scope
- abi/win64.c ABI description data; ABI lowering of params/returns (regs + stack), shadow space, 16-byte alignment.
- x64 machine IR with virtual regs; baseline isel; fixed-register assignment (BOOTSTRAP-SHORTCUT); prologue/epilogue; `--emit=mc`.

## Acceptance
- [ ] mc golden tests; encoded function bytes for `return 42` match expectation.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T025-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

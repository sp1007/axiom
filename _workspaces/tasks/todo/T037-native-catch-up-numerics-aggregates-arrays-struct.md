---
id: T037
title: Native catch-up: numerics, aggregates, arrays, struct ABI
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
depends: [T036]
priority: 57
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/abi, bootstrap/axiom0/src/target/x64, tests/run/native_aggr]
spec: [0189, 0230, 0250, 0181]
---
# T037 — Native catch-up: numerics, aggregates, arrays, struct ABI

## Goal
All numeric/struct/array tests pass natively.

## Scope
- Sign/zero extension, all widths, overflow checks (jo), div-by-zero checks, memcpy-like lowering, Win64 aggregate passing (by value ≤8 bytes pow2, else by reference to copy) and hidden return pointer, bounds check traps.

## Acceptance
- [ ] Differential green for all run tests.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T037-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

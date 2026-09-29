---
id: T065
title: FFI: extern "C"/"system", @repr(C), DLL imports
phase: P8-backend
owner: axiom-backend
reviewer: axiom-qa
depends: [T062]
priority: 92
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/abi, bootstrap/axiom0/src/link, bootstrap/axiom0/src/types/ffi, tests/run/ffi, tests/ui/ffi]
spec: [0094, 0195, tasks/0292, tasks/0336, 0104]
---
# T065 — FFI: extern "C"/"system", @repr(C), DLL imports

## Goal
Call Windows APIs and C functions; export Axiom functions.

## Scope
- extern declarations, unsafe call rules, @repr(C) structs across the boundary, `@link("kernel32")`-style import libraries resolved by our linker (import table generation for arbitrary DLL functions), exports.

## Acceptance
- [ ] run tests calling GetTickCount/WriteFile/etc.; ui tests for unsafe violations.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T065-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

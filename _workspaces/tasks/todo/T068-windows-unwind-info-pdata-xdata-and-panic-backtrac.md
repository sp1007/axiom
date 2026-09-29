---
id: T068
title: Windows unwind info (.pdata/.xdata) and panic backtrace basics
phase: P8-backend
owner: axiom-backend
reviewer: axiom-qa
depends: [T063]
priority: 95
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/target/x64/unwind, bootstrap/axiom0/src/link/pe, tests/run/unwind]
spec: [0188, 0190]
---
# T068 — Windows unwind info (.pdata/.xdata) and panic backtrace basics

## Goal
Make generated code debugger/unwinder friendly on Windows.

## Scope
- UNWIND_INFO per function from frame lowering, .pdata/.xdata sections, exception directory; optional minimal symbolisation for panic messages.

## Acceptance
- [ ] objdump shows valid pdata; a debugger (or RtlLookupFunctionEntry test via FFI) finds every function.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T068-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

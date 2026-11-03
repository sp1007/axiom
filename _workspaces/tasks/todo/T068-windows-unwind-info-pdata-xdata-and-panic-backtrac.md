---
id: T068
title: E17.3 Windows unwind info (.pdata/.xdata) and panic backtrace basics
phase: P17-debugging-runtime-introspecti
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217]
priority: 95
status: todo
attempts: 0
paths: [compiler/target/x64, compiler/link, tests/run/unwind]
spec: [0188, 0190]
covers: [REQ-ERR-001, REQ-ERR-002, REQ-ERR-003]
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
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Roadmap epic E17.3 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; the phase planning task may split it, keeping this id for the first slice.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:59 covers += REQ-ERR-001, REQ-ERR-002, REQ-ERR-003 (metadata only)

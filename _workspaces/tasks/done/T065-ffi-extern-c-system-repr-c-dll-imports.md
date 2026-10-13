---
id: T065
title: FFI: extern "C"/"system", @repr(C), DLL imports
phase: P8-backend
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T060, T061b]
priority: 82
status: done
attempts: 1
paths: [bootstrap/axiom0/src/abi, bootstrap/axiom0/src/link, bootstrap/axiom0/src/types/ffi, bootstrap/axiom0/src/resolve, bootstrap/axiom0/src/hir, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/interp, tests/run/ffi, tests/ui/ffi]
locks: [bootstrap/axiom0/src/diag/codes/FFI.def, bootstrap/axiom0/src/diag/codes/LINK.def, bootstrap/axiom0/src/driver/pipeline.c]
spec: [0094, 0195, tasks/0292, tasks/0336, 0104]
started: 2026-10-13 16:33:00
finished: 2026-10-13 17:37:25
---
# T065 — FFI: extern "C"/"system", @repr(C), DLL imports

## Goal
Call Windows APIs and C functions from native code.

## Scope
- extern declarations, unsafe call rules, @repr(C) structs across the boundary, `@link("kernel32")`-style import libraries resolved by our linker (import table generation for arbitrary DLL functions, calls through the IAT in instruction selection). Exported symbols and DLL output are E18.7.
- `extern` items (parsed by T012, lowered by T015b) through resolution, type checking (`types/ffi`), MIR calls to imported symbols.
- **Direct FFI is native-only** (ADR-0002 §4): when the interpreter reaches an `extern` call it reports AX_FFI_NOT_IN_ORACLE; such run tests use `// modes: native` with the reason "direct FFI is native-only (ADR-0002)". Code that must run in both modes goes through the host intrinsics (T061c).

## Acceptance
- [ ] Native run tests calling `GetTickCount64`, `GetCurrentProcessId`, `WriteFile` (prints `Xin chào thế giới`, byte-exact) and a `@repr(C)` struct passed by pointer; ui tests for unsafe violations; an interp run of an `extern` call gives AX_FFI_NOT_IN_ORACLE.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T065-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Starts as soon as the language features it needs exist (ROADMAP R8), not after the whole P7 gate.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-13 16:33:00 started (attempt 1) 
- 2026-10-13 17:37:25 accepted by QA -> done

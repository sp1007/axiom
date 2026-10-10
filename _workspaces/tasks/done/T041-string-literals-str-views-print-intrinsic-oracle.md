---
id: T041
title: String literals, Str views, print intrinsic (oracle)
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T039]
priority: 61
status: done
attempts: 1
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, bootstrap/axiom0/src/driver, bootstrap/axiom0/src/resolve, tests/]
locks: [bootstrap/axiom0/src/diag/codes/TYPE.def]
spec: [0089, tasks/0332, 0045, 0152]
started: 2026-10-10 10:19:34
finished: 2026-10-10 10:55:38
---
# T041 — String literals, Str views, print intrinsic (oracle)

## Goal
Static string data and output, first stdout-observable programs.

## Scope
- String literals → static read-only data, `Str` as a built-in read-only (ptr,len) value for literals (T048b folds it into the view/slice rules, 0263 §39), built-in `len(s)` (ADR-0006 §3), byte strings, `print(s)`/`print_int(n)` as declared intrinsics (library-level later), interp writes to stdout.

## Acceptance
- [ ] Interp run test prints `Xin chào thế giới` (stdout compared as exact UTF-8 bytes); `Str` length of the literal is its byte length (22) per the text spec, character iteration deferred to std.
- [ ] run tests with `// stdout:` directives in interp mode; they carry `// native-after: T042` (removed by T042).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T041-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-10 10:19:34 started (attempt 1) 
- 2026-10-10 10:55:38 accepted by QA -> done

---
id: T041
title: String literals, Str views, print intrinsic (oracle)
phase: P5-language
owner: axiom-semantics
reviewer: axiom-qa
depends: [T039]
priority: 61
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/str]
spec: [0089, tasks/0332, 0045, 0152]
---
# T041 — String literals, Str views, print intrinsic (oracle)

## Goal
Static string data and output, first stdout-observable programs.

## Scope
- String literals → static read-only data, `Str` as (ptr,len) view type, byte strings, `print(s)`/`print_int(n)` as declared intrinsics (library-level later), interp writes to stdout.

## Acceptance
- [ ] run tests with `// stdout:` directives in interp mode.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T041-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

---
id: T067
title: E18.6 Linker v2: separate compilation, multiple objects, archives
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
depends: [T218]
priority: 94
status: todo
attempts: 0
paths: [compiler/link, compiler/driver, tests/link2]
spec: [0164, 0217, 0099, tasks/0369]
---
# T067 — Linker v2: separate compilation, multiple objects, archives

## Goal
Per-module objects linked together; libraries.

## Scope
- One object per module, symbol resolution across objects, duplicate/undefined diagnostics, COFF archive (.lib) reading for our own libraries, section GC of unreferenced functions.

## Acceptance
- [ ] Multi-module projects build via separate objects; byte-identical rebuilds.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T067-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Roadmap epic E18.6 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; the phase planning task may split it, keeping this id for the first slice.
- 
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

---
id: T009
title: Diagnostics engine (model, code registry, human + JSON renderers)
phase: P1-kernel
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T008, T002, T112]
priority: 15
status: done
attempts: 1
paths: [bootstrap/axiom0/src/diag, tests/unit/diag]
spec: [0146, tasks/0360, tasks/0421, 0153]
started: 2026-10-05 15:56:48
unblocks: 1
finished: 2026-10-05 16:02:28
---
# T009 — Diagnostics engine (model, code registry, human + JSON renderers)

## Goal
Diagnostics as data, rendered by the driver in human or JSON form.

## Scope
- Diagnostic{code, severity, primary span, labels[], notes[], helps[], fixits[]}; DiagSink collecting in memory; deterministic ordering (file, offset, code).
- Code registry split by area (ADR-0005 §2): `diag/codes/<AREA>.def` X-macro files, one per area of spec/diagnostics.md, all created here (seeded; an area with no code yet gets an empty file) and included by `diag/codes.def`. Later tasks add codes only to their area file (their `locks:` entry) and never edit `codes.def`.
- Human renderer: `error[AX_TYPE_MISMATCH]: msg` + `--> file:line:col` + source line + caret/underline, labels, notes; JSON renderer (schema from spec/diagnostics.md).

## Acceptance
- [ ] Unit/golden tests of both renderers incl. multi-line spans, tabs, CRLF, unicode.
- [ ] Unknown code use is a compile-time error in C (X-macro enum).
- [ ] Every area of spec/diagnostics.md has its file; adding a code to one area file needs no other edit to be usable (shown by a unit test).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T009-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 15:31:19 started (attempt 1) T009-impl
- 2026-10-05 15:49:29 block: needs bootstrap/axiom0/src/kernel/base.c in paths to fix archcheck failure
- 2026-10-05 15:51:17 unblocked (cycle 1) 
- 2026-10-05 15:56:48 started (attempt 1) T009-impl
- 2026-10-05 16:02:28 accepted by QA -> done

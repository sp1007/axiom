---
id: T009
title: Diagnostics engine (model, code registry, human + JSON renderers)
phase: P1-kernel
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T008, T002]
priority: 15
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/diag, tests/unit/diag]
spec: [0146, tasks/0360, tasks/0421, 0153]
---
# T009 — Diagnostics engine (model, code registry, human + JSON renderers)

## Goal
Diagnostics as data, rendered by the driver in human or JSON form.

## Scope
- Diagnostic{code, severity, primary span, labels[], notes[], helps[], fixits[]}; DiagSink collecting in memory; deterministic ordering (file, offset, code).
- diag/codes.def X-macro registry seeded from spec/diagnostics.md.
- Human renderer: `error[AX_TYPE_MISMATCH]: msg` + `--> file:line:col` + source line + caret/underline, labels, notes; JSON renderer (schema from spec/diagnostics.md).

## Acceptance
- [ ] Unit/golden tests of both renderers incl. multi-line spans, tabs, CRLF, unicode.
- [ ] Unknown code use is a compile-time error in C (X-macro enum).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T009-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

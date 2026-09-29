---
id: T071
title: Text: Str, String, formatting minimal, Bytes
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
depends: [T070]
priority: 102
status: todo
attempts: 0
paths: [std/text, tests/std/text]
spec: [0089, tasks/0332, 0045, 0304]
---
# T071 — Text: Str, String, formatting minimal, Bytes

## Goal
UTF-8 text model per spec.

## Scope
- Str/String/Bytes APIs, UTF-8 validation, int/float to string, concatenation, comparison, simple `format`/print helpers per spec.

## Acceptance
- [ ] Text tests round-trip `Xin chào thế giới`: byte length 22, 17 Unicode scalar values, validation, slicing on char boundaries, invalid UTF-8 rejected.
- [ ] run tests incl. multi-byte text.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T071-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

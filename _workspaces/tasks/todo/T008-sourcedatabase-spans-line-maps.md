---
id: T008
title: SourceDatabase, spans, line maps
phase: P1-kernel
owner: axiom-frontend
reviewer: axiom-qa
depends: [T007]
priority: 14
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/source, tests/unit/source]
spec: [0153, 0172, 0171]
---
# T008 — SourceDatabase, spans, line maps

## Goal
Load source files (and virtual files for tests) with FileId, byte spans and line maps.

## Scope
- load_file / add_virtual_file, content hash, canonical path, UTF-8 validation (invalid UTF-8 → diagnostic later), BOM handling, CRLF handling (spans are bytes; line map treats CRLF as one break).
- LineMap: byte offset ↔ line/column (column in Unicode scalar values and in bytes).

## Acceptance
- [ ] Unit tests for CRLF, BOM, empty file, multi-byte characters, last line without newline.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T008-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

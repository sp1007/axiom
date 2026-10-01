---
id: T071c
title: UTF-8 ↔ UTF-16 conversion (for Windows W APIs)
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T071]
priority: 102
status: todo
attempts: 0
paths: [std/text/utf16, tests/std/utf16]
spec: [0089, tasks/0332]
covers: []
---
# T071c — UTF-8 ↔ UTF-16 conversion (for Windows W APIs)

## Goal
Text conversion at the OS boundary: Axiom strings are UTF-8, Windows W APIs take UTF-16 (split from T071; used by T074/T074b and by the native host functions).

## Scope
- UTF-8 → UTF-16 and UTF-16 → UTF-8 with surrogate pairs; strict version (error on a lone surrogate or invalid UTF-8) and lossy version (U+FFFD) per 0089; NUL-terminated wide buffer helper for API calls.

## Acceptance
- [ ] UTF-16 round trip of `Xin chào thế giới` and of U+1F600 (surrogate pair D83D DE00); a lone surrogate is an error in strict mode and U+FFFD in lossy mode.
- [ ] Both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T071c-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Both modes are mandatory. The only accepted reason for a `// modes: native` test is "direct FFI is native-only (ADR-0002)"; heavy tests (≥ 100k elements) may be native-only if a small interp twin of the same test exists.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

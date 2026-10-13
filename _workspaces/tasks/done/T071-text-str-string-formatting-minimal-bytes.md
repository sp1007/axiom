---
id: T071
title: Text core: Str, String, UTF-8, char primitives
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T070]
priority: 102
status: done
attempts: 1
paths: [std/text, tests/std/text]
spec: [0089, tasks/0332, 0045, tasks/0304]
covers: [REQ-STD-176]
started: 2026-10-13 20:23:49
finished: 2026-10-13 21:10:05
---
# T071 — Text core: Str, String, UTF-8, char primitives

## Goal
UTF-8 text model per spec.

## Scope
- Str/String APIs: UTF-8 validation, concatenation, comparison, slicing on char boundaries, `StringBuilder`-style growth (`push_str`, `push_char`, reserve).
- char primitives: `decode_char_at(bytes, i) -> (char, len)`, `char.len_utf8`, `char.encode_utf8`, `char_count`, `is_char_boundary`.
- Split (ADR-0005 §8): `ByteBuf`, integer formatting/parsing and `format` helpers are T071b; UTF-8 ↔ UTF-16 is T071c. Float formatting belongs to E12.2.

## Acceptance
- [ ] Text tests round-trip `Xin chào thế giới`: byte length 22, 17 Unicode scalar values, validation, slicing on char boundaries, invalid UTF-8 rejected.
- [ ] run tests incl. multi-byte text, in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T071-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Both modes are mandatory. The only accepted reason for a `// modes: native` test is "direct FFI is native-only (ADR-0002)"; heavy tests (≥ 100k elements) may be native-only if a small interp twin of the same test exists.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:21 covers += REQ-STD-176 (metadata only)
- 2026-10-13 20:23:49 started (attempt 1) 
- 2026-10-13 21:10:05 accepted by QA -> done

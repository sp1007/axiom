---
id: T071
title: Text: Str, String, formatting minimal, Bytes
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T070]
priority: 102
status: todo
attempts: 0
paths: [std/text, tests/std/text]
spec: [0089, tasks/0332, 0045, tasks/0304]
---
# T071 — Text: Str, String, formatting minimal, Bytes

## Goal
UTF-8 text model per spec.

## Scope
- Str/String/Bytes APIs, UTF-8 validation, integer to string (float formatting belongs to E12.2), concatenation, comparison, simple `format`/print helpers per spec.
- `StringBuilder`-style growth, integer formatting in decimal/hex/binary with width and zero-padding, integer parsing with overflow errors, `ByteBuf` (growable bytes) with little-endian `put_u8/u16/u32/u64/i32/i64`, `patch_u32_at` (for relocations/headers), and byte-slice views; char primitives (`decode_char_at(bytes, i) -> (char, len)`, `char.len_utf8`, `char.encode_utf8`, `char_count`, `is_char_boundary`); UTF-8 ↔ UTF-16 conversion with surrogate pairs (for Windows W APIs, used by T074; strict version errors on lone surrogates, lossy version replaces them with U+FFFD per 0089). Needed by the self-hosted compiler (self-host std subset, SPEC-00 / T003a).

## Acceptance
- [ ] ByteBuf LE writers produce exact bytes (golden tests); formatting/parsing round-trips at MIN/MAX of every width.
- [ ] Text tests round-trip `Xin chào thế giới`: byte length 22, 17 Unicode scalar values, validation, slicing on char boundaries, invalid UTF-8 rejected.
- [ ] UTF-16 round trip of `Xin chào thế giới` and of U+1F600 (surrogate pair D83D DE00); a lone surrogate is an error in strict mode and U+FFFD in lossy mode.
- [ ] run tests incl. multi-byte text.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T071-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

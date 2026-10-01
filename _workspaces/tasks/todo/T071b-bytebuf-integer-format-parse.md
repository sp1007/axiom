---
id: T071b
title: ByteBuf, integer formatting and parsing, format helpers
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T071]
priority: 102
status: todo
attempts: 0
paths: [std/text/fmt, std/bytes, tests/std/fmt, tests/std/bytes]
spec: [0089, tasks/0332, 0045, tasks/0304]
covers: []
---
# T071b — ByteBuf, integer formatting and parsing, format helpers

## Goal
The byte-level and number-formatting half of the self-host std subset (split from T071): what an object writer, a linker and a diagnostics renderer written in Axiom need.

## Scope
- `ByteBuf` (growable bytes) with little-endian `put_u8/u16/u32/u64/i32/i64`, `patch_u32_at` (relocations, headers), alignment padding, byte-slice views.
- Integer → text in decimal/hex/binary with width and zero-padding for every integer width; integer parsing with overflow and invalid-digit errors as `Result`.
- Simple `format`/print helpers per spec (no float formatting — E12.2).

## Acceptance
- [ ] ByteBuf LE writers produce exact bytes (golden tests); `patch_u32_at` out of range is an error, not a write.
- [ ] Formatting/parsing round-trips at MIN/MAX of every width; hex dump helper output matches a golden file.
- [ ] Both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T071b-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Both modes are mandatory. The only accepted reason for a `// modes: native` test is "direct FFI is native-only (ADR-0002)"; heavy tests (≥ 100k elements) may be native-only if a small interp twin of the same test exists.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

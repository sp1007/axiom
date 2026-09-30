---
id: T074
title: std.io / fs / env / process for hosted Windows
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T071, T065]
priority: 105
status: todo
attempts: 0
paths: [std/io, std/fs, std/env, std/process, tests/std/io]
spec: [tasks/0330, tasks/0335, 0220, 0221]
---
# T074 — std.io / fs / env / process for hosted Windows

## Goal
Enough OS access to write a compiler in Axiom.

## Scope
- stdout/stderr writers, read/write whole files, command-line args, environment, exit, errors as Result types.
- **Unicode at the OS boundary:** Axiom strings are UTF-8; every Windows call that takes or returns text uses the W API (`CreateFileW`, `GetCommandLineW` + `CommandLineToArgvW`, `GetEnvironmentVariableW`, `FindFirstFileW`/`FindNextFileW`, `CreateDirectoryW`, `DeleteFileW`, `GetFileAttributesExW`) with T071's UTF-8 ↔ UTF-16 conversion. Never the A APIs: they go through the ANSI code page and break Vietnamese names.
- Binary file read/write (whole file and streaming writer), `std.path` (join, parent, file name, extension, normalisation, Windows separators), directory listing (sorted), create directory, remove file, file-exists/metadata, monotonic clock `Instant` for `--time-passes`. Needed by the self-hosted compiler (self-host std subset, SPEC-00 / T003a).

## Acceptance
- [ ] A test program writes a small binary file with ByteBuf and reads it back byte-identical; directory listing is sorted and deterministic.
- [ ] std.io print/println of `Xin chào thế giới` correct on console, pipe and file; file written and read back byte-identical.
- [ ] Unicode paths and args: create, list, read back and delete `thư mục/tệp_tiếng_Việt.ax` (and a name with U+1F600); a program run with argument `xin chào` sees exactly those UTF-8 bytes; an environment variable with a Vietnamese value round-trips.
- [ ] run tests using temp files.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T074-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

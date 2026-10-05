---
id: T074b
title: std.fs / path / directories / monotonic clock for hosted Windows
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T074]
priority: 106
status: todo
attempts: 0
paths: [std/fs, std/path, std/time, std/sys/windows/fs.ax, std/sys/windows/time.ax, tests/std/fs, tests/run/host/fs]
spec: [tasks/0330, tasks/0335, 0220, 0221]
covers: [REQ-STD-173, REQ-STD-174]
---
# T074b — std.fs / path / directories / monotonic clock for hosted Windows

## Goal
The rest of the OS surface the compiler driver needs (split from T074): file system operations, paths and timing.

## Scope
- `std.path` (join, parent, file name, extension, normalisation, Windows separators); streaming binary file writer; directory listing (sorted), create directory, remove file, file-exists/metadata; monotonic clock `Instant` (integer nanoseconds, no floats) for `--time-passes`.
- Native host functions in `std/sys/windows/fs.ax` and `time.ax` (`FindFirstFileW`/`FindNextFileW`, `CreateDirectoryW`, `DeleteFileW`, `GetFileAttributesExW`, `QueryPerformanceCounter`), W APIs only, T071c conversion.

## Acceptance
- [ ] A test program writes a small binary file with ByteBuf and reads it back byte-identical; directory listing is sorted and deterministic.
- [ ] Unicode paths: create, list, read back and delete `thư mục/tệp_tiếng_Việt.ax` (and a name with U+1F600).
- [ ] `Instant` differences are non-negative and a 50 ms busy loop measures between 20 and 2000 ms.
- [ ] `grep -rn "native-after: T074b" tests` prints nothing; all tests in both modes, using temp directories.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T074b-report.md` with exact `## Files changed`.

## Out of scope
- Async IO, sockets, memory mapping, signals (P21).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Both modes are mandatory. The only accepted reason for a `// modes: native` test is "direct FFI is native-only (ADR-0002)"; heavy tests (≥ 100k elements) may be native-only if a small interp twin of the same test exists.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:21 covers += REQ-STD-173, REQ-STD-174 (metadata only)

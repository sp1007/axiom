---
id: T074
title: std.io / env / process for hosted Windows
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T071b, T071c, T065, T061c]
priority: 105
status: done
attempts: 1
paths: [std/io, std/env, std/process, std/sys/windows/io.ax, std/sys/windows/process.ax, tests/std/io, tests/run/host/io]
spec: [tasks/0330, tasks/0335, 0220, 0221]
started: 2026-10-13 23:33:16
finished: 2026-10-14 00:21:09
---
# T074 — std.io / env / process for hosted Windows

## Goal
Enough OS access to write a compiler in Axiom.

## Scope
- stdout/stderr writers, `print`/`println`, read/write whole files (text and binary), command-line args, environment, exit, errors as Result types — all through the host intrinsics (ADR-0002), so every test runs under the oracle and natively.
- Native host functions `__ax_host_*` for stdio, open/read/write/close/file_size, args, env and exit in `std/sys/windows/io.ax` and `process.ax`, over kernel32/shell32 FFI.
- **Unicode at the OS boundary:** Axiom strings are UTF-8; every Windows call that takes or returns text uses the W API (`CreateFileW`, `GetCommandLineW` + `CommandLineToArgvW`, `GetEnvironmentVariableW`) with T071c conversion. Never the A APIs: they go through the ANSI code page and break Vietnamese names.
- Console output (ADR-0006 §9): `WriteConsoleW` with UTF-8 → UTF-16 conversion when the handle is a console, `WriteFile` with raw bytes for pipes and files.
- Split (ADR-0005 §8): paths, directories, metadata, remove/mkdir, streaming binary writer and the clock are T074b.

## Acceptance
- [ ] std.io print/println of `Xin chào thế giới`: byte-exact on a pipe and in a file (gate); on a console checked by `python tools/tests/console_check.py` (T042 helper; SKIP only if no console can be allocated).
- [ ] A file written and read back is byte-identical (text and binary).
- [ ] A program run with argument `xin chào` sees exactly those UTF-8 bytes (runner directive `args:`); an environment variable with a Vietnamese value round-trips (`env:`).
- [ ] `grep -rn "native-after: T074" tests` prints nothing; all tests in both modes.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T074-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Both modes are mandatory. The only accepted reason for a `// modes: native` test is "direct FFI is native-only (ADR-0002)"; heavy tests (≥ 100k elements) may be native-only if a small interp twin of the same test exists.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-13 23:33:16 started (attempt 1) 
- 2026-10-14 00:21:09 accepted by QA -> done

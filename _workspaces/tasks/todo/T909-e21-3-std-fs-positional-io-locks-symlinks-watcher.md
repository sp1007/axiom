---
id: T909
title: E21.3 Complete std.fs & std.path: positional read_at/write_at, file locks, symlinks, tempfiles & fs watcher
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T908]
priority: 219
status: todo
attempts: 0
paths: [std/fs/ext, std/fs/watch, std/fs/tempfile, tests/run/std_fs_complete]
spec: [spec/SPEC-122-os-fs-process-signals-ipc.md, tasks/0335, tasks/0443, tasks/0840]
covers: [REQ-STD-173, REQ-RT-144, REQ-RT-158, REQ-RT-159, REQ-RT-160]
---
# T909 — E21.3 Complete std.fs & std.path: positional read_at/write_at, file locks, symlinks, tempfiles & fs watcher

## Goal
Implement positional random-access file I/O (`read_at`, `write_at`), file locking, symlinks/permissions, secure `TempFile`/`TempDir`, atomic write-and-rename, and directory change watching in `std.fs` per `spec/SPEC-122-os-fs-process-signals-ipc.md`.

## Scope
- Implement `std/fs/ext` adding `read_at` and `write_at` (`OVERLAPPED` offset on Windows / `pread64`/`pwrite64` on Linux without altering seek position; `REQ-RT-159`), `sync_all`/`sync_data` (`FlushFileBuffers` / `fsync`; `REQ-RT-160`), `FileLock` (`LockFileEx`/`UnlockFileEx` and `flock`), and symlink/junction/permissions metadata (`REQ-STD-173`).
- Implement `std/fs/tempfile` (`TempFile`, `TempDir`, and `AtomicWriteFile` that stages to a sibling temporary file, flushes data, and atomically replaces the destination via `MoveFileExW(..., MOVEFILE_REPLACE_EXISTING)` / `renameat`).
- Implement `std/fs/watch` (`FsWatcher` backed by `ReadDirectoryChangesW` on Windows and `inotify` on Linux, plus deterministic oracle virtual events).
- Add run tests in `tests/run/std_fs_complete`.

## Acceptance
- [ ] Run tests in `tests/run/std_fs_complete` verify `read_at`/`write_at` cursor invariance, exclusive/shared `FileLock` contention, `TempDir` auto-cleanup on `Drop`, `AtomicWriteFile` crash-safe replacement, and `FsWatcher` events in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T909-report.md` with exact `## Files changed`.

## Out of scope
- Process pipelines, signals, IPC, and Windows ConPTY `WriteConsoleW` (`T910`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T909/build` and `python tools/axtest.py --compiler build-snap-T909/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)

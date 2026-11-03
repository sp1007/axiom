---
id: T651
title: E16.9 — Linux x86-64 syscall host interface (std.sys.linux) & WSL test runner integration
phase: P16-targets-platforms
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T066, T313, T650]
priority: 94
status: todo
attempts: 0
paths: [std/sys/linux, compiler/driver/target_linux, tests/run/linux_std, tests/selfhost/driver]
locks: [tools/axtest.py]
spec: [spec/SPEC-80-linux-x86-64-elf-static.md, spec/SPEC-04-core-extensibility.md, 0192, 0220]
covers: [REQ-TGT-096, REQ-TGT-097, REQ-TGT-098, REQ-TGT-099, REQ-TGT-100]
---
# T651 — E16.9 — Linux x86-64 syscall host interface (std.sys.linux) & WSL test runner integration

## Goal
Implement the native Linux x86-64 syscall backend for `std/core/host.ax` in `std/sys/linux`, wire `--target x86_64-linux` stdlib platform selection in the compiler driver, and integrate WSL execution into `tools/axtest.py`.

## Scope
- Implement `__ax_host_*` host-interface functions in `std/sys/linux` using direct Linux x86-64 syscalls (`SYS_mmap`/`SYS_munmap`/`SYS_mremap` for `heap_alloc`/`heap_realloc`/`heap_free`, `SYS_openat`/`SYS_read`/`SYS_write`/`SYS_close`/`SYS_fstat` for stdio & file I/O, `SYS_getdents64`/`SYS_mkdir`/`SYS_unlink`/`SYS_newfstatat` for filesystem operations, `SYS_clock_gettime` for `monotonic_ns`, `/proc/self/exe` `SYS_readlink` & initial stack `argc`/`argv`/`envp` capture in `_start` for `args_count`/`arg`/`env_get`/`exe_path`, `SYS_clone`/`SYS_futex`/`SYS_nanosleep`/`SYS_sched_yield` for threads & futexes, and `SYS_exit_group` for `exit`).
- Map Linux `-errno` values (`ENOENT`, `EACCES`/`EPERM`, `EEXIST`, `EINVAL`/`EBADF`, `ETIMEDOUT`) to the canonical negated host error kinds of `SPEC-04 AXS-EXT-110`.
- Wire `compiler/driver/target_linux` so `--target x86_64-linux` links `std/sys/linux` instead of `std/sys/windows`.
- Update `tools/axtest.py` to support `--target x86_64-linux` test execution on Linux hosts natively and on Windows hosts via `wsl` when available (cleanly skipping execution when `wsl` is unavailable while still verifying ELF64 build artifacts).

## Acceptance
- [ ] `std`-using Axiom programs (`Vec`, `String`, `HashMap`, `fs`, `io`, `process`, `time`, UTF-8 `Xin chào thế giới` output) compile with `--target x86_64-linux` and pass under Linux / WSL.
- [ ] Positive and negative tests in `tests/run/linux_std` and `tests/selfhost/driver` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T651-report.md` with exact `## Files changed`.

## Out of scope
- Dynamic `libc`/`dlopen` interop (`T659`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:35:00 created by T216 (P16 phase planning)

---
id: T683
title: E16.8 — Hermetic cross-target SDK/import stubs & 3-level OS platform layer (std.os.* & std.sys.*)
phase: P16-targets-platforms
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T651, T667, T670, T675, T679, T682]
priority: 126
status: todo
attempts: 0
paths: [std/os, compiler/link/sysroot, tests/std/os_platform, tests/selfhost/link]
spec: [spec/SPEC-88-cross-compilation-platform-layer.md, 0097, 0220, tasks/0336, tasks/0453, tasks/0587]
covers: [REQ-TOOL-001, REQ-TGT-320, REQ-TGT-324, REQ-TGT-325]
---
# T683 — E16.8 — Hermetic cross-target SDK/import stubs & 3-level OS platform layer (std.os.* & std.sys.*)

## Goal
Implement built-in hermetic cross-target OS import stubs and sysroot discovery in `compiler/link/sysroot` (`REQ-TOOL-001`) and implement the Level-2 explicit platform modules (`std.os.windows`, `std.os.linux`, `std.os.macos`, `std.os.android`, `std.os.wasi`) in `std/os`.

## Scope
- Implement `compiler/link/sysroot`:
  - Provide built-in hermetic system import stub tables for Windows (`kernel32.dll`, `ntdll.dll`, `ws2_32.dll`, `bcrypt.dll`), Linux (`libc.so.6`, `libm.so.6`, `libdl.so.2`, `libpthread.so.0`), Android (`libc.so`, `libm.so`, `libdl.so`, `liblog.so`), macOS (`libSystem.B.dylib`), and WASI (`wasi_snapshot_preview1`) so `axiomc` produces linked executables and dynamic libraries for any target from any host without third-party C compilers or OS SDKs (`REQ-TOOL-001`).
  - Support optional `--sysroot <dir>` and `-L <dir>` search paths when linking against user-supplied foreign C libraries.
- Implement `std/os` (`0220 §1–16`):
  - `std.os.windows`: raw `Handle`, console mode helpers, Win32 exit/error bridges.
  - `std.os.linux`: `RawFd`, `AsRawFd`/`FromRawFd`, Linux-specific open/mmap/futex flags.
  - `std.os.macos`: `RawFd`, Mach timebase and Darwin path helpers.
  - `std.os.android`: `RawFd`, Android log priorities (`__android_log_write`) and API-level queries.
  - `std.os.wasi`: WASI `Fd`, preopen directory descriptors, and capability rights.
  - Gate each platform module with `@cfg(target_os = "...")` while keeping portable `std.*` (`Level 1`) completely free of OS-specific types.
- Add tests in `tests/std/os_platform` and `tests/selfhost/link`.

## Acceptance
- [ ] A single host `axiomc` binary cross-compiles and links a `std`-using program (`Xin chào thế giới` + `std.fs` + `std.env`) for `x86_64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `aarch64-android`, `wasm32`, and `riscv64-linux` without invoking any external C compiler or system linker (`REQ-TOOL-001`).
- [ ] Positive and negative tests in `tests/std/os_platform` and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T683-report.md` with exact `## Files changed`.

## Out of scope
- Full cross-compilation conformance suite (`T684`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:43:00 created by T216 (P16 phase planning)

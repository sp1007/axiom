---
id: T667
title: E16.4 — Mach-O 64 executable & .dylib linker, dyld chained fixups, ad-hoc codesign & std.sys.macos
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T663, T666]
priority: 110
status: todo
attempts: 0
paths: [compiler/link/macho, std/sys/macos, tests/link/macho, tests/selfhost/link]
spec: [spec/SPEC-84-macos-aarch64-macho.md, 0196, 0220, tasks/0453, tasks/0563]
covers: [REQ-TGT-303, REQ-TGT-311, REQ-TGT-312, REQ-TGT-313]
---
# T667 — E16.4 — Mach-O 64 executable & .dylib linker, dyld chained fixups, ad-hoc codesign & std.sys.macos

## Goal
Implement the native Mach-O 64 linker (`MH_EXECUTE` and `MH_DYLIB`, `dyld` chained fixups, export trie, and self-contained SHA-256 ad-hoc `LC_CODE_SIGNATURE` signing) in `compiler/link/macho` and the `std/sys/macos` host-interface implementation over `libSystem.B.dylib`.

## Scope
- Implement the Mach-O 64 linker in `compiler/link/macho` without requiring Xcode or `ld64`:
  - 16 KiB (`0x4000`) page-aligned `__PAGEZERO`, `__TEXT`, `__DATA_CONST`, `__DATA`, and `__LINKEDIT` segments for `MH_EXECUTE` (`LC_MAIN`, `LC_LOAD_DYLINKER` `/usr/lib/dyld`) and `MH_DYLIB` (`LC_ID_DYLIB`, `@rpath/lib<name>.dylib`).
  - `__TEXT,__stubs` + `__DATA_CONST,__got` synthesis for imported `libSystem.B.dylib` and external `.dylib` symbols, `LC_DYLD_CHAINED_FIXUPS` pointer-chain encoding (`DYLD_CHAINED_PTR_64_OFFSET`), and ULEB128 radix-tree `LC_DYLD_EXPORTS_TRIE`.
  - Built-in `.tbd` stub parser and `libSystem.B.dylib` export catalog so cross-linking from Windows or Linux requires no macOS SDK installation (`0196 §15`).
  - Self-contained ad-hoc `LC_CODE_SIGNATURE` generator (`CS_MAGIC_EMBEDDED_SIGNATURE`, `CS_MAGIC_CODEDIRECTORY` with SHA-256 hashes over every 4 KiB page up to the signature offset, `CS_ADHOC | CS_LINKER_SIGNED`) so Apple Silicon macOS executes the binary directly.
- Implement `std/sys/macos` (`__ax_host_*` functions implemented via `libSystem.B.dylib`: `malloc`/`realloc`/`free`, `open`/`read`/`write`/`close`/`fstat`, `opendir`/`readdir`/`closedir`/`mkdir`/`unlink`/`stat`, `mach_continuous_time` / `clock_gettime_nsec_np`, `_NSGetExecutablePath`, `_NSGetArgc`/`_NSGetArgv`/`getenv`, `pthread_create`/`pthread_join`/`__ulock_wait`/`__ulock_wake`, `_exit`).
- Add linker and cross-build tests in `tests/link/macho` and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc build --target aarch64-macos` and `axiomc build --target aarch64-macos --kind dll` emit valid 16 KiB-aligned, ad-hoc code-signed Mach-O 64 `MH_EXECUTE` and `MH_DYLIB` binaries without external linker or Xcode tools.
- [ ] Positive and negative tests in `tests/link/macho` and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T667-report.md` with exact `## Files changed`.

## Out of scope
- Universal Mach-O fat binaries (`E16.11`, `T690`–`T691`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:39:00 created by T216 (P16 phase planning)

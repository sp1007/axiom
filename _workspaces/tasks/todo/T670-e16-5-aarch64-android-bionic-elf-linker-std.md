---
id: T670
title: E16.5 — aarch64-android target descriptor, 16 KiB page-aligned Bionic ELF PIE/.so linker & std.sys.android
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T663, T669]
priority: 113
status: todo
attempts: 0
paths: [compiler/target/aarch64/android, compiler/link/elf_android, std/sys/android, tests/obj/android, tests/selfhost/link]
spec: [spec/SPEC-85-android-aarch64-jni.md, 0198, 0220, tasks/0453]
covers: [REQ-TGT-073, REQ-TGT-076, REQ-TGT-077, REQ-TGT-078]
---
# T670 — E16.5 — aarch64-android target descriptor, 16 KiB page-aligned Bionic ELF PIE/.so linker & std.sys.android

## Goal
Implement the `aarch64-android` target descriptor, NDK-free Bionic ELF64 PIE/`.so` linker specialization (16 KiB `PT_LOAD` alignment, `.note.android.ident`, `/system/bin/linker64`), and `std/sys/android` platform implementation.

## Scope
- Implement the `aarch64-android` `TargetDesc` in `compiler/target/aarch64/android`: reserve `X18` (Android ShadowCallStack register), track target `api_level` (default `29`), and configure `ET_DYN` as the mandatory image format for both executables and shared libraries.
- Implement the Android ELF64 linker specialization in `compiler/link/elf_android`:
  - Emit `.note.android.ident` (recording Android API level and NDK-compatible ABI tag), `PT_INTERP` `/system/bin/linker64` for PIE executables, `DT_SONAME` for `.so` libraries, `PT_GNU_RELRO` + `DT_BIND_NOW`, and 16 KiB (`0x4000`) `p_align` on `PT_LOAD` segments.
  - Embed built-in Bionic stub symbol definitions for `libc.so`, `libm.so`, `libdl.so`, and `liblog.so` so `axiomc build --target aarch64-android` links without an external Android NDK installation (`0198 §4`).
- Implement `std/sys/android` providing `__ax_host_*` host-interface functions over Bionic `libc.so` and `__android_log_write` diagnostic integration.
- Add tests in `tests/obj/android` and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc build --target aarch64-android` and `axiomc build --target aarch64-android --kind dll` emit valid 16 KiB page-aligned ELF64 PIE and `.so` artifacts with `.note.android.ident` and Bionic `DT_NEEDED` entries on any host without an Android NDK.
- [ ] Positive and negative tests in `tests/obj/android` and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T670-report.md` with exact `## Files changed`.

## Out of scope
- JNI binding layer (`std.ffi.jni`) and `@jni_export` (`T671`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:40:00 created by T216 (P16 phase planning)

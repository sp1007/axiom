---
id: T663
title: E16.3 — AArch64 32-bit instruction encoder, ELF64 AArch64 relocations/veneers & Linux AArch64 std.sys
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T651, T659, T662]
priority: 106
status: todo
attempts: 0
paths: [compiler/target/aarch64/encode, compiler/obj/elf_aarch64, compiler/link/elf_aarch64, std/sys/linux_aarch64, tests/encode/aarch64, tests/selfhost/encode, tests/selfhost/obj, tests/selfhost/link]
spec: [spec/SPEC-83-aarch64-linux.md, 0193, tasks/0521, tasks/0784]
covers: [REQ-TGT-134, REQ-TGT-148, REQ-TGT-149, REQ-TGT-150, REQ-TGT-151, REQ-TGT-152, REQ-TGT-153, REQ-TGT-154]
---
# T663 — E16.3 — AArch64 32-bit instruction encoder, ELF64 AArch64 relocations/veneers & Linux AArch64 std.sys

## Goal
Implement the deterministic 32-bit little-endian AArch64 instruction encoder, ELF64 `EM_AARCH64` object writer and linker (including page/offset relocations and range-extension veneers), and `std/sys/linux_aarch64` syscall backend for `--target aarch64-linux`.

## Scope
- Implement the 32-bit fixed-width AArch64 machine code encoder in `compiler/target/aarch64/encode` (data processing immediate/register, branches `B`/`BL`/`B.cond`/`CBZ`/`CBNZ`/`TBZ`/`TBNZ`/`BR`/`BLR`/`RET`, load/store single and pair `LDR`/`STR`/`LDP`/`STP`, atomics `LDXR`/`STLXR`/`LDAR`/`STLR`/`CAS`/`DMB`, scalar FP, and NEON SIMD encodings) plus branch-offset relaxation for `B.cond`/`CBZ`/`TBZ` exceeding ±1 MiB / ±32 KiB.
- Implement ELF64 `EM_AARCH64` (`183`) object emission in `compiler/obj/elf_aarch64` and static/dynamic linking in `compiler/link/elf_aarch64` (`R_AARCH64_ABS64`, `R_AARCH64_PREL32`, `R_AARCH64_CALL26`, `R_AARCH64_JUMP26`, `R_AARCH64_ADR_PREL_PG_HI21`, `R_AARCH64_ADD_ABS_LO12_NC`, `R_AARCH64_LDST8..128_ABS_LO12_NC`, `R_AARCH64_ADR_GOT_PAGE`, `R_AARCH64_LD64_GOT_LO12_NC`, AArch64 PLT stubs using `ADRP X16` + `LDR X17` + `BR X17`, and ±128 MiB long-branch veneers).
- Implement `std/sys/linux_aarch64` (`SVC #0` with Linux generic AArch64 syscall numbers in `X8`, e.g., `SYS_openat = 56`, `SYS_read = 63`, `SYS_write = 64`, `SYS_exit_group = 94`, `SYS_mmap = 222`, and AArch64 `_start` entry point).
- Add encoding, object, and linker tests in `tests/encode/aarch64`, `tests/selfhost/encode`, `tests/selfhost/obj`, and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc build --target aarch64-linux` emits deterministic ELF64 `EM_AARCH64` objects, static executables, PIE executables, and `.so` libraries whose instruction encodings match reference disassembler vectors.
- [ ] Positive and negative tests in `tests/encode/aarch64`, `tests/selfhost/encode`, `tests/selfhost/obj`, and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T663-report.md` with exact `## Files changed`.

## Out of scope
- macOS Mach-O (`E16.4`), Android JNI (`E16.5`), and Windows ARM64 PE (`E16.12`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:38:00 created by T216 (P16 phase planning)

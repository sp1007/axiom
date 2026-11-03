---
id: T661
title: E16.3 — Canonical AArch64 ISA backend, AAPCS64 ABI & aarch64-linux ELF64 specification (SPEC-83)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T313, T653]
priority: 104
status: todo
attempts: 0
paths: [spec/SPEC-83-aarch64-linux.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-81-target-desc-isa-conformance.md, 0193, tasks/0521, tasks/0784]
covers: [REQ-TGT-113, REQ-TGT-114, REQ-TGT-115, REQ-TGT-116, REQ-TGT-117, REQ-TGT-118, REQ-TGT-119, REQ-TGT-120, REQ-TGT-121, REQ-TGT-122]
---
# T661 — E16.3 — Canonical AArch64 ISA backend, AAPCS64 ABI & aarch64-linux ELF64 specification (SPEC-83)

## Goal
Consolidate the canonical specification for Axiom's AArch64 (ARM64) backend architecture, `CallConv.Aapcs64` calling convention, 32-bit fixed-width instruction selection/encoding, NEON SIMD & atomic lowering, and `aarch64-linux` ELF64 object/image format into `spec/SPEC-83-aarch64-linux.md` (`AXS-A64-*` rule IDs).

## Scope
- Write `spec/SPEC-83-aarch64-linux.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-A64-NNN` rules (`0193`, `tasks/0521` `AARM-20..70`).
- Specify the AArch64 `RegisterFile`: `X0..X30` (64-bit) / `W0..W30` (32-bit) aliasing (`AARM-24`), dedicated stack pointer `SP` (`AARM-25`), zero registers `XZR`/`WZR` (`AARM-26`), frame pointer `X29` (`FP`), link register `X30` (`LR`, `AARM-34`), intra-procedure call scratch `X16`/`X17` (`IP0`/`IP1`), platform register `X18`, FP/SIMD registers `V0..V31` (`Q/D/S/H/B` views, `AARM-41`), and `NZCV` condition flags (`AARM-27`).
- Specify the `CallConv.Aapcs64` calling convention (`0193 §5–8`, `AARM-29..37`): integer/pointer args in `X0..X7`, FP/SIMD and Homogeneous Floating-point/Short-Vector Aggregates (`HFA`/`HVA` up to 4 elements) in `V0..V7`, composites `<= 16` bytes in up to 2 GPRs, indirect result address in `X8` (`XR` / `sret`, not consuming `X0`, `AARM-32`), callee-saved `X19..X28` and low 64 bits `D8..D15` of `V8..V15`, 16-byte `SP` alignment at all public interfaces (`AARM-37`), no red zone on Linux (`AARM-36`), and `STP X29, X30, [SP, #-N]!` / `LDP` frame lowering.
- Specify AArch64 instruction selection, immediate materialization (12-bit shifted arithmetic immediates, bitmask logical immediates, `MOVZ`/`MOVN`/`MOVK` 16-bit chunk sequences), addressing modes (`[base, #imm]`, pre/post-indexed, register offset with shift/extend, `ADRP` + `:lo12:` `ADD`/`LDR`), checked arithmetic overflow (`ADDS`/`SUBS`/`B.VS`, `SMULL`/`UMULL` high-half checks), atomics (`LDXR`/`STLXR` LL/SC loops, `LDAR`/`STLR` acquire/release, optional Armv8.1-A `+lse` `CAS`/`LDADD`/`SWP`, `DMB ISH`, `AARM-46..48`), and 128-bit NEON vector lowering.
- Specify `aarch64-linux` ELF64 (`EM_AARCH64 = 183`): relocations (`R_AARCH64_ABS64`, `R_AARCH64_PREL32`, `R_AARCH64_CALL26`, `R_AARCH64_JUMP26`, `R_AARCH64_ADR_PREL_PG_HI21`, `R_AARCH64_ADD_ABS_LO12_NC`, `R_AARCH64_LDST8..128_ABS_LO12_NC`, `R_AARCH64_ADR_GOT_PAGE`, `R_AARCH64_LD64_GOT_LO12_NC`, `R_AARCH64_TLSLE_ADD_TPREL_HI12`/`LO12_NC`), ±128 MiB `B`/`BL` range-extension veneers (`AARM-56`), and Linux AArch64 syscalls (`X8` syscall number, `X0..X5` args, `SVC #0`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-83-aarch64-linux.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-A64-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T661-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of AArch64 (`T662`, `T663`) and Apple/Android/Windows ARM64 specializations (`E16.4`, `E16.5`, `E16.12`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:38:00 created by T216 (P16 phase planning)

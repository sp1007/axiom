---
id: T664
title: E16.3 — AArch64 Linux encoding, AAPCS64 ABI & QEMU/WSL-ARM64 execution conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T663]
priority: 107
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_3_aarch64_linux]
spec: [spec/SPEC-83-aarch64-linux.md, 0193, tasks/0521, tasks/0784]
covers: [REQ-TGT-155, REQ-TGT-156, REQ-TGT-157, REQ-TGT-158, REQ-TGT-159, REQ-TGT-160, REQ-TGT-161, REQ-TGT-162, REQ-TGT-163, REQ-TGT-164, REQ-TGT-165]
---
# T664 — E16.3 — AArch64 Linux encoding, AAPCS64 ABI & QEMU/WSL-ARM64 execution conformance suite

## Goal
Certify the E16.3 exit criterion (`ROADMAP.md` §3): `aarch64-linux` instruction encoding accuracy, AAPCS64 ABI compliance, ELF64 `EM_AARCH64` static and dynamic linking, and behavioral equivalence between `x86_64` and `aarch64` (`AARM-63`).

## Scope
- Create `tests/conformance/p16/e16_3_aarch64_linux` covering:
  - AArch64 instruction encoding golden vectors (verified against `aarch64-linux-gnu-objdump` / reference disassembler byte tables for integer, bitmask immediate, `ADRP`+`:lo12:`, `STP`/`LDP`, LL/SC & LSE atomic, FP, and NEON instructions).
  - AAPCS64 calling convention conformance: `X0..X7` and `V0..V7` parameter passing, `HFA`/`HVA` 2..4 lane float/vector structs, `<= 16`-byte composite passing in GPR pairs, `> 16`-byte composite indirect passing, `X8` (`XR`) indirect `sret` returns (verifying `X0` is still used for the first regular argument), callee-saved `X19..X28` and `D8..D15` preservation, and 16-byte `SP` alignment.
  - ELF64 `EM_AARCH64` relocation and veneer tests (`R_AARCH64_ADR_PREL_PG_HI21` page boundary crossings, ±128 MiB `CALL26` veneer generation, GOT/PLT dynamic resolution).
  - Differential execution of `aarch64-linux` binaries (under `qemu-aarch64` / native ARM64 Linux when available) against `--interp` and `x86_64` native.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_3_aarch64_linux` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T664-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T662`–`T663`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin chào thế giới` for greeting strings.

## Log
- 2026-11-03 08:38:00 created by T216 (P16 phase planning)

---
id: T680
title: E16.7 — RISC-V 64 RV64GC encoding, LP64D ABI, PCREL hi20/lo12 linking & conformance suite
phase: P16-targets-platforms
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T313, T679]
priority: 123
status: todo
attempts: 0
paths: [tests/conformance/p16/e16_7_riscv64]
spec: [spec/SPEC-87-riscv64-linux.md, 0152, tasks/0522, tasks/0784]
covers: [REQ-TGT-197, REQ-TGT-198, REQ-TGT-199, REQ-TGT-200, REQ-TGT-201, REQ-TGT-202, REQ-TGT-203, REQ-TGT-204, REQ-TGT-205, REQ-TGT-206]
---
# T680 — E16.7 — RISC-V 64 RV64GC encoding, LP64D ABI, PCREL hi20/lo12 linking & conformance suite

## Goal
Certify the E16.7 exit criterion (`ROADMAP.md` §3): `riscv64-linux` tier-2 target backend conformance across `RV64GC` + `RVC` encoding, flagless branch/overflow semantics, `LP64D` calling convention, paired `PCREL_HI20`/`LO12` ELF64 linking, and cross-target semantic equivalence (`ABACKEND-51..60`).

## Scope
- Create `tests/conformance/p16/e16_7_riscv64` covering:
  - `RV64GC` and 16-bit `RVC` instruction encoding golden vectors (verified against `riscv64-linux-gnu-objdump` / reference disassembler byte tables, including negative tests around the `0x800` 12-bit signed immediate boundary in `LUI`+`ADDI` and `AUIPC`+`ADDI`).
  - Flagless comparison and checked arithmetic overflow tests (`i8..i128`, `u8..u128`, 32-bit sign-extension invariant in 64-bit registers for `u32` values >= `0x8000_0000`).
  - `LP64D` psABI calling convention tests (`a0..a7`, `fa0..fa7`, mixed `{i32, f64}` and `{f32, f32}` hardware FP struct flattening, `> 16`-byte by-reference structs, `s0..s11` and `fs0..fs11` preservation, `x0`/`gp`/`tp` untouched).
  - ELF64 `EM_RISCV` static executable, `.a` archive, and `.so` dynamic library linking tests, plus execution under `qemu-riscv64` when available and differential verification against `--interp`.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p16/e16_7_riscv64` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T680-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation changes (belong in `T678`–`T679`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). All Axiom test programs use canonical syntax (`axiom-syntax`): `=` only, `.` paths only, and `Xin chào thế giới` for greeting strings.

## Log
- 2026-11-03 08:42:00 created by T216 (P16 phase planning)

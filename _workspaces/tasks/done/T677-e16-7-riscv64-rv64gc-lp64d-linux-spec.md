---
id: T677
title: E16.7 — Canonical RISC-V 64 (RV64GC) backend, LP64D ABI & riscv64-linux ELF64 specification (SPEC-87)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T511, T653]
priority: 120
status: done
attempts: 1
paths: [spec/SPEC-87-riscv64-linux.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-81-target-desc-isa-conformance.md, 0152, tasks/0522, tasks/0784]
covers: [REQ-TGT-166, REQ-TGT-167, REQ-TGT-168, REQ-TGT-169, REQ-TGT-170, REQ-TGT-171, REQ-TGT-172, REQ-TGT-173, REQ-TGT-174, REQ-TGT-175]
started: 2026-11-04 03:16:29
finished: 2026-11-04 04:40:54
---
# T677 — E16.7 — Canonical RISC-V 64 (RV64GC) backend, LP64D ABI & riscv64-linux ELF64 specification (SPEC-87)

## Goal
Consolidate the canonical specification for Axiom's `riscv64-linux` (`RV64GC`) backend, flagless condition/branch architecture, `LP64D` psABI calling convention, `RV64IMAFDC` instruction encoding, paired `PCREL_HI20`/`LO12` ELF64 relocations, and Linux RISC-V syscall boundary into `spec/SPEC-87-riscv64-linux.md` (`AXS-RV64-*` rule IDs).

## Scope
- Write `spec/SPEC-87-riscv64-linux.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-RV64-NNN` rules (`0152 §59`, `tasks/0522` `ABACKEND-20..60`, `tasks/0784`).
- Specify the `riscv64-linux` baseline ISA (`RV64GC` = `RV64IMAFD_Zicsr_Zifencei_C`; optional features `+v`, `+zba`, `+zbb`, `+zbs`) and `RegisterFile` (`tasks/0522 §6–14`): `x0` (`zero`, hardwired 0), `x1` (`ra`, return address), `x2` (`sp`, 16-byte aligned stack pointer), `x3` (`gp`, unallocatable global pointer), `x4` (`tp`, unallocatable TLS pointer), `x8` (`s0`/`fp`), caller-saved `t0..t6` (`x5..x7`, `x28..x31`) and `a0..a7` (`x10..x17`), callee-saved `s0..s11` (`x8..x9`, `x18..x27`), and FP registers `f0..f31` (`ft0..ft11`, `fa0..fa7`, callee-saved `fs0..fs11`, `ABACKEND-45`).
- Specify the flagless comparison and overflow model (`tasks/0522 §15–19`, `ABACKEND-22..23`): RISC-V has no architectural condition-flags register; boolean comparisons use `SLT`/`SLTU`/`SLTI`/`SLTIU`/`SEQZ`/`SNEZ`, conditional branches fuse comparisons into `BEQ`/`BNE`/`BLT`/`BGE`/`BLTU`/`BGEU`, and checked signed/unsigned arithmetic overflow is synthesized via explicit two-register sequences without relying on CPU carry/overflow flags.
- Specify the RISC-V `LP64D` psABI (`CallConv.RiscV`): `a0..a7` integer/pointer and `fa0..fa7` hardware FP parameter/return registers, hardware FP struct flattening (`{f32/f64}`, `{f32/f64, f32/f64}`, `{int, f32/f64}`), composites `<= 16` bytes in up to 2 GPRs, `> 16`-byte composites passed by reference, caller/callee sign-extension of 32-bit `i32` AND `u32` values in 64-bit registers (`ADDW`/`SUBW`/`MULW`/`SLLIW`), 16-byte stack alignment, and no red zone.
- Specify RV64GC + 16-bit RVC compressed instruction encoding (`ABACKEND-43, 46`), ELF64 `EM_RISCV = 243` (`EF_RISCV_RVC | EF_RISCV_FLOAT_ABI_DOUBLE`), paired `AUIPC` + load/store/addi relocations (`R_RISCV_PCREL_HI20` + `R_RISCV_PCREL_LO12_I`/`R_RISCV_PCREL_LO12_S` where the `LO12` symbol points to the `AUIPC` label, valid without mandatory linker relaxation `ABACKEND-47`), `R_RISCV_CALL_PLT`, `R_RISCV_GOT_HI20`, and Linux RISC-V syscalls (`a7` syscall number, `a0..a5` args, `ecall`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-87-riscv64-linux.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-RV64-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T677-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of the RISC-V64 backend (`T678`, `T679`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:42:00 created by T216 (P16 phase planning)
- 2026-11-04 03:16:29 started (attempt 1) T677-impl
- 2026-11-04 04:40:54 accepted by QA -> done

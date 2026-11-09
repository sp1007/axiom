---
id: T534
title: E13.1 Canonical unsafe asm(...) HIR/MIR/LIR representation, verification & x86-64 codegen
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T501, T504]
priority: 164
status: todo
attempts: 0
paths: [compiler/syntax, compiler/hir, compiler/mir, compiler/target/x64, tests/run/inline_asm]
locks: [compiler/verify/verifier.ax, compiler/interp/interp.ax, compiler/diag/codes/UNSAFE.def]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-OWNER-008, REQ-ABI-102]
---
# T534 — E13.1 Canonical unsafe asm(...) HIR/MIR/LIR representation, verification & x86-64 codegen

## Goal
Implement canonical typed inline assembly `unsafe asm(...)` across the full compilation pipeline (HIR, MIR, LIR, and x86-64 machine code), with operand ownership verification and a deterministic trap in the MIR interpreter oracle.

## Scope
- Add canonical inline assembly parsing in `compiler/syntax` and HIR lowering:
  `unsafe asm("inst template", in("reg") val, out("reg") res, inout("reg") var, clobbers("flags", "memory"))`
  (strictly adhering to canonical Axiom syntax: no bang-macro `asm!`, no `::`, no `:=`).
- Lower inline assembly into `compiler/mir` as `MirStatement.InlineAsm` and into `compiler/target/x64` as `LirInst.InlineAsm`.
- Verify clobber specifications, register constraint legality, and operand move/view ownership in `compiler/verify/verifier.ax`.
- In `compiler/interp/interp.ax`, executing an `unsafe asm(...)` statement deterministically halts execution and emits diagnostic `AX_VERIFY_INLINE_ASM_IN_ORACLE`.
- Lower constraints to x86-64 registers (`rax`, `rcx`, `rdx`, `rbx`, `rsi`, `rdi`, `r8`..`r15`, `xmm0`..`xmm15`), handle memory clobbers as optimization fences, and encode binary instructions directly.

## Acceptance
- [ ] `tests/run/inline_asm/x64_basic.ax` runs natively on Windows x64, verifying `CPUID`, `RDTSC`, and register constraint dataflow.
- [ ] `tests/run/inline_asm/interp_trap.ax` verifies that executing inline assembly under `--interp` reports `AX_VERIFY_INLINE_ASM_IN_ORACLE` without crashing.
- [ ] Full test suite passes in `build-snap-T534` under `axiomc2.exe`.
- [ ] Report `_workspaces/reports/T534-report.md` with exact `## Files changed`.

## Out of scope
- Non-x86 architectures (AArch64 inline assembly is delivered in P16 `T664a`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`), ADR-0039.
- All code uses canonical syntax (`=` for bindings, `.` for paths).

## Log
- 2026-11-09 created for ADR-0039 P13 inline assembly integration

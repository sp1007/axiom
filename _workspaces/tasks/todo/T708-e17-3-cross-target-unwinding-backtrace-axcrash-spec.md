---
id: T708
title: E17.3 Canonical cross-target frame unwind metadata, panic backtraces & AXCRASH minidump specification (SPEC-94)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316]
priority: 178
status: todo
attempts: 0
paths: [spec/SPEC-94-unwinding-backtraces.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0188, tasks/0700, tasks/0525, tasks/1057]
covers: [REQ-DBG-117, REQ-DBG-120]
---
# T708 — E17.3 Canonical cross-target frame unwind metadata, panic backtraces & AXCRASH minidump specification (SPEC-94)

## Goal
Consolidate the canonical specification for Axiom target-independent UnwindPlan, Windows .pdata/.xdata, ELF .eh_frame/.eh_frame_hdr, Mach-O __unwind_info, std.backtrace, and AXCRASH crash/minidump reporting into spec/SPEC-94-unwinding-backtraces.md (AXS-UNW-* rules).

## Scope
- Write `spec/SPEC-94-unwinding-backtraces.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-UNW-NNN` rules.
- Specify the target-independent `UnwindPlan` derived directly from machine `FramePlan` (`0188 §1–32`, `ADEBUG-81`, `ADEBUG-95`): explicit `Prologue`, `Body`, and `Epilogue` machine-IR regions (`AEPI-20`..`AEPI-23`), leaf vs non-leaf classification (`AUNW-20`..`AUNW-21`), frame-pointer omission rules (`ADEBUG-41`), and post-RA verification that machine optimizations never invalidate unwind metadata (`AUNW-31`).
- Specify Windows x64 (`0188 §15–56`: `.pdata` sorted `RUNTIME_FUNCTION` RVAs, `.xdata` `UNWIND_INFO` v1/v2, `UWOP_PUSH_NONVOL`, `UWOP_ALLOC_SMALL`, `UWOP_ALLOC_LARGE`, `UWOP_SET_FPREG`, `UWOP_SAVE_NONVOL`, `UWOP_SAVE_XMM128`, canonical unwind-recognizable epilogues, mandatory `__chkstk` page probing ≥ 4 KiB `AUNW-37`) and Windows ARM64 (`.pdata`/`.xdata` packed and unpacked ARM64 unwind codes).
- Specify ELF `.eh_frame` + `.eh_frame_hdr` DWARF Call Frame Information (`CIE`/`FDE`, `DW_CFA_def_cfa`, `DW_CFA_def_cfa_offset`, `DW_CFA_offset`, sorted binary-search header table across x86-64, AArch64, and RISC-V64) and Mach-O `__TEXT,__unwind_info` compact unwind encodings (`UNWIND_ARM64_MODE_FRAMELESS`, `UNWIND_ARM64_MODE_FRAME`, `UNWIND_ARM64_MODE_DWARF`).
- Specify `std.backtrace` (`Backtrace.capture`, frame cursor walking without heap allocation on the panic path) and `AXCRASH` (`tasks/1057`: fault classification, x86-64/AArch64/RISC-V64 register capture, stack memory window capture, deterministic crash fingerprint, and portable `.dmp`/`.axcrash` dump generation).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-94-unwinding-backtraces.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-UNW-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T708-report.md` with exact `## Files changed`.

## Out of scope
- Windows `.pdata`/`.xdata` implementation (`T068`) and ELF/Mach-O/`std.backtrace`/`AXCRASH` implementation (`T709`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

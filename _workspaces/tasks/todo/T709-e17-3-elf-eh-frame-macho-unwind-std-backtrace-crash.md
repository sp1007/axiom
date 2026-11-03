---
id: T709
title: E17.3 ELF .eh_frame/.eh_frame_hdr DWARF CFI, Mach-O __unwind_info, std.backtrace & AXCRASH minidump runtime
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T068]
priority: 180
status: todo
attempts: 0
paths: [compiler/obj/eh_frame, compiler/link/eh_frame_hdr, std/backtrace, std/crash, tests/run/backtrace]
spec: [spec/SPEC-94-unwinding-backtraces.md, 0188, tasks/0700, tasks/0525, tasks/1057]
covers: [REQ-DBG-117, REQ-DBG-120]
---
# T709 — E17.3 ELF .eh_frame/.eh_frame_hdr DWARF CFI, Mach-O __unwind_info, std.backtrace & AXCRASH minidump runtime

## Goal
Implement ELF .eh_frame/.eh_frame_hdr DWARF CFI and Mach-O __unwind_info emission from UnwindPlan, cross-target std.backtrace stack walking, and the AXCRASH crash/minidump runtime.

## Scope
- Implement `compiler/obj/eh_frame` and `compiler/link/eh_frame_hdr` lowering `UnwindPlan` to deterministic DWARF CFI `CIE`/`FDE` records, sorted `.eh_frame_hdr` binary-search lookup tables (`PT_GNU_EH_FRAME`), and Mach-O `__TEXT,__unwind_info` compact unwind sections across `x86_64-linux`, `aarch64-linux`, `aarch64-android`, `riscv64-linux`, and `aarch64-macos`.
- Implement `std.backtrace` (`Backtrace.capture`, `BacktraceFrame`, allocation-free cursor stepping over Windows `.pdata`, ELF `.eh_frame_hdr`, Mach-O `__unwind_info`, and WASM shadow-stack frames) integrated with the panic handler.
- Implement `std.crash` (`AXCRASH` runtime: structured panic/signal/SEH fault handler, register and stack-frame capture, semantic crash fingerprinting, and portable minidump / `.axcrash` bundle writer).
- Add cross-target stack walking and crash-report tests in `tests/run/backtrace`.

## Acceptance
- [ ] `axiomc build` emits valid `.eh_frame`/`.eh_frame_hdr` on ELF targets and `__unwind_info` on Mach-O targets.
- [ ] `std.backtrace.Backtrace.capture()` and panic handlers accurately walk multi-frame call stacks and emit `AXCRASH` crash reports in `tests/run/backtrace`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T709-report.md` with exact `## Files changed`.

## Out of scope
- Symbolication of raw frame addresses into inline source lines (`T712`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

---
id: T710
title: E17.3 Cross-target unwinding, std.backtrace & AXCRASH minidump conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T709]
priority: 181
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_3_unwinding_backtrace]
spec: [spec/SPEC-94-unwinding-backtraces.md, 0188, tasks/0700, tasks/0525, tasks/1057]
covers: [REQ-DBG-117, REQ-DBG-120]
---
# T710 — E17.3 Cross-target unwinding, std.backtrace & AXCRASH minidump conformance suite

## Goal
Certify the E17.3 exit criteria: structural unwind metadata validity across Windows, ELF, Mach-O, and WASM, panic backtrace completeness, and AXCRASH dump generation.

## Scope
- Create `tests/conformance/p17/e17_3_unwinding_backtrace` covering:
-   - Windows x64 and ARM64 `.pdata`/`.xdata` verification (`AUNW-20`..`AUNW-38`, `AEPI-20`..`AEPI-23`): leaf omission, non-leaf `UWOP_PUSH_NONVOL` / `UWOP_ALLOC_SMALL` / `UWOP_ALLOC_LARGE` / `UWOP_SAVE_XMM128`, `__chkstk` > 4 KiB frames, sorted RVAs, and native `RtlLookupFunctionEntry` + `RtlVirtualUnwind` walking.
-   - ELF `.eh_frame`/`.eh_frame_hdr` (`x86_64-linux`, `aarch64-linux`, `riscv64-linux`) and Mach-O `__unwind_info` (`aarch64-macos`) CFI table verification with frame-pointer omission (`-fomit-frame-pointer`).
-   - `std.backtrace` multi-frame stack capture, `Drop` cleanup execution across `panic=unwind` frames (`ADEBUG-72`), FFI boundary stop guards, and `AXCRASH` minidump / `.axcrash` report verification.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_3_unwinding_backtrace` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T710-report.md` with exact `## Files changed`.

## Out of scope
- Interactive debugger CLI stepping (`T714`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

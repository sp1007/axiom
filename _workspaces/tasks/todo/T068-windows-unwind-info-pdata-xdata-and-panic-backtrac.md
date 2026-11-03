---
id: T068
title: E17.3 Windows unwind info (.pdata/.xdata) and panic backtrace basics
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T708]
priority: 179
status: todo
attempts: 0
paths: [compiler/target/x64/unwind, compiler/obj/pe_unwind, compiler/link/pe_pdata, tests/run/unwind, tests/selfhost/unwind]
spec: [spec/SPEC-94-unwinding-backtraces.md, 0188, 0190, tasks/0700, tasks/1057]
covers: [REQ-ERR-001, REQ-ERR-002, REQ-ERR-003, REQ-DBG-117, REQ-DBG-120]
---
# T068 — E17.3 Windows unwind info (.pdata/.xdata) and panic backtrace basics

## Goal
Make generated code debugger and unwinder compliant on Windows x64 and Windows ARM64 by deriving `UnwindPlan` directly from `FramePlan` and emitting deterministic `.pdata` and `.xdata` sections.

## Scope
- Derive target-independent `UnwindPlan` from `FramePlan` during Windows x64 and ARM64 frame lowering (`Prologue`, `Body`, and `Epilogue` structural verifier per `0188 §30`, `UWOP_PUSH_NONVOL`, `UWOP_ALLOC_SMALL`, `UWOP_ALLOC_LARGE`, `UWOP_SET_FPREG`, `UWOP_SAVE_NONVOL`, `UWOP_SAVE_XMM128`, and mandatory `__chkstk` probing for frames ≥ 4 KiB) in `compiler/target/x64/unwind`.
- Emit deterministic `.pdata` (`RUNTIME_FUNCTION` image-relative RVAs) and `.xdata` (`UNWIND_INFO` v1/v2) sections in COFF objects (`compiler/obj/pe_unwind`) and populate `IMAGE_DIRECTORY_ENTRY_EXCEPTION` in PE `.exe`/`.dll` images (`compiler/link/pe_pdata`).
- Implement Windows stack walking (`RtlCaptureContext`, `RtlLookupFunctionEntry`, `RtlVirtualUnwind`) for panic backtraces and add unit/run tests in `tests/selfhost/unwind` and `tests/run/unwind`.

## Acceptance
- [ ] `objdump` / PE inspection shows valid sorted `.pdata` and `.xdata` tables; `RtlLookupFunctionEntry` and `RtlVirtualUnwind` walk every non-leaf function frame in `tests/run/unwind` and `tests/selfhost/unwind`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T068-report.md` with exact `## Files changed`.

## Out of scope
- ELF `.eh_frame`/`.eh_frame_hdr`, Mach-O `__unwind_info`, cross-target `std.backtrace`, and `AXCRASH` minidump writer (`T709`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Roadmap epic E17.3 (moved out of the C core by ROADMAP R7: not needed for self-hosting). Implemented in `compiler/` (Axiom) after T087; refined by T217 to depend on `T316` and `T708` (`SPEC-94`).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:59 covers += REQ-ERR-001, REQ-ERR-002, REQ-ERR-003 (metadata only)
- 2026-11-03 09:25:00 refined by T217 (fixed phase typo, added T316 and T708 depends, narrowed paths, added REQ-DBG-117 and REQ-DBG-120 covers)

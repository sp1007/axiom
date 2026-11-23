---
id: T513
title: E13.3 — Freestanding startup, static init order, custom section layout & CRT-free native image emission
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T512, T537]
priority: 162
status: todo
attempts: 0
timeout_min: 480
paths: [compiler/lir, compiler/target/x64, compiler/obj, compiler/link, tests/link/freestanding]
locks: [compiler/driver/pipeline.ax, compiler/backend/session.ax, compiler/types/typeck.ax, compiler/mir/mir.ax, compiler/mir/builder.ax, compiler/abi/win64.ax, compiler/interp_opt/session.ax, compiler/interp/interp.ax, compiler/interp/frame.ax]
spec: [spec/SPEC-52-freestanding-runtime-composition.md, 0143, 0097, tasks/0370, tasks/0455]
covers: [REQ-ABI-055, REQ-ABI-056, REQ-ABI-083, REQ-RES-145, REQ-CAP-140, REQ-CAP-143]
started: 2026-11-23 09:11:08
unblocks: 1
---
# T513 — E13.3 — Freestanding startup, static init order, custom section layout & CRT-free native image emission

## Goal
Emit CRT-free and `kernel32.dll`-free native binaries in `--profile freestanding`, lowering `@entry`, `@naked`, `@section("...")`, `@used`, and deterministic const-initialized statics through LIR, COFF object emission, and the linker.

## Scope
- Lower `@entry` as the direct PE/image entry point without emitting the hosted startup stub (`axiom_start`) or default `KERNEL32.dll` import table when `--profile freestanding` or `--profile kernel` is active (`SPEC-52 AXS-FRE-010`, `AXS-FRE-023`), and execute `@entry` in `--interp` (`0 WEAK-NATIVE`).
- Lower `@naked` functions without prologue/epilogue/stack-probe generation (`AXS-FRE-013`, rejecting nonzero local stack frames with `AX_TYPE_INVALID_NAKED_FN`) and lower `extern "interrupt"` functions via `CallingConventionDescription` metadata (`REQ-ABI-078`, `AXS-FRE-015`: hardware interrupt frame binding, full modified-GPR preservation, and `IRETQ`).
- Const-evaluate and emit deterministic const-initialized `static` / `static mut` items (`.rdata`, `.data`, `.bss`), custom named sections for `@section("...")` (`fn` and `static`), `@no_mangle` verbatim symbols, `@used` GC roots (`LGC_ROOT_USED`), and `@panic_handler` / `@global_allocator` hooks (with freestanding `UD2` trap fallback instead of `KERNEL32.dll`-backed `axiom_panic`) across MIR, LIR, `ObjModel`, the PE32+ linker, and `--interp`.

## Acceptance
- [ ] Link and objdump tests in `tests/link/freestanding` verify that a `--profile freestanding` executable has zero DLL imports (`objdump -p` shows no import directory), uses the `@entry` symbol as its entry point, places `@section` items in their named COFF sections, retains `@used` items under section GC, and runs natively and in `--interp` (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T513-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- **Build on `T537`'s process-wide `MIR_LOCAL_STATIC` & `.rdata`/`.data`/`.bss` pipeline**: `T537` (`depends: [T512, T537]`) delivers `MIR_LOCAL_STATIC` (`6u8`), non-TLS `HIR_ITEM_STATIC` const-evaluation, `--interp` process-wide static slots, and hosted `.rdata`/`.data`/`.bss` emission. Extend that pipeline directly for `--profile freestanding` and `--profile kernel`: custom `@section("...")` COFF section routing on `fn` and `static`, `@no_mangle` verbatim symbols, `@used` GC roots (`LGC_ROOT_USED`), and `@panic_handler` / `@global_allocator` static dispatch hooks without introducing a competing `MIR_LOCAL_CONST` static representation.
- Const-evaluate allowed non-TLS `HIR_ITEM_STATIC` initializers at all three `is_tls` gates in `compiler/types/typeck.ax` (`lines 3217, 12664, 13612`), serialize aggregate `HIR_ITEM_STATIC` constants in `compiler/backend/session.ax:backend_populate_hir_const_aggregates`, and accept allowed `HIR_ITEM_STATIC` items in `compiler/interp_opt/session.ax:session_comptime_check_and_eval`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T513/build` and `python tools/axtest.py --compiler build-snap-T513/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:02:00 created by T213 (P13 phase planning)
- 2026-11-23 09:11:08 started (attempt 1) axiom-backend
- 2026-11-23 09:20:16 block: Requires locks outside current paths (driver/pipeline.ax, backend/session.ax, types/typeck.ax, mir/mir.ax, mir/builder.ax, abi/win64.ax, interp_opt/session.ax, interp/interp.ax); two overlap active T517
- 2026-11-23 09:31:00 architect (T513-unblock): verified E13.3 seams against SPEC-52 and INV-LAYER-002; widened locks to the exact 9 upstream/interp files (incl. interp/frame.ax) and added timeout_min 480
- 2026-11-23 09:34:01 unblocked (cycle 1) 
- 2026-11-23 17:35:00 architect (T537-unblock): depends += T537 so freestanding static sections/hooks build directly on T537's MIR_LOCAL_STATIC pipeline

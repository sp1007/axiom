---
id: T413
title: E11.3 — @thread_local statics, COFF/PE .tls emission & thread-local storage
phase: P11-concurrency-async
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T090]
priority: 135
status: doing
attempts: 1
paths: [std/thread/local.ax, tests/run/concurrency/tls, tests/ui/concurrency/tls]
locks: [compiler/diag/code.ax, compiler/hir/hir.ax, compiler/hir/lower.ax, compiler/types/typeck.ax, compiler/own/unsafe.ax, compiler/mir/mir.ax, compiler/mir/builder.ax, compiler/verify/verifier.ax, compiler/interp/interp.ax, compiler/interp/oracle.ax, compiler/lir/lir.ax, compiler/lir/builder.ax, compiler/target/x64/encode.ax, compiler/target/x64/frame.ax, compiler/target/x64/isel.ax, compiler/target/x64/mod.ax, compiler/backend/session.ax, compiler/driver/pipeline.ax, compiler/obj/coff.ax, compiler/obj/writer.ax, compiler/link/pe.ax, compiler/link/linker.ax, compiler/link/mod.ax, std/thread/mod.ax, tests/selfhost]
spec: [spec/SPEC-32-threads-sync.md, spec/SPEC-04-core-extensibility.md, 0136, 0203, tasks/0329, tasks/0623]
covers: [REQ-CONC-030, REQ-CONC-110]
started: 2026-11-09 14:59:11
unblocks: 1
agent: T413-impl
---
# T413 — E11.3 — @thread_local statics, COFF/PE .tls emission & thread-local storage

## Goal
Implement `@thread_local` statics and `std.thread.LocalKey<T>` across HIR, MIR, the interpreter oracle, and the Windows x64 COFF/PE `.tls` backend.

## Scope
- Enable `@thread_local` attribute lowering in `compiler/hir/lower.ax` and `compiler/types/typeck.ax` (`AXS-EXT-091`), enforcing that TLS items are `!Share` and cannot be borrowed via an escaping `view<T>` that outlives the current thread (`0136 §53`).
- Lower TLS place accesses in MIR/LIR to section `Tls` (`AXS-EXT-071`) with `TlsRel` relocations (`AXS-EXT-073`), emit `.tls$` sections and the PE TLS directory (`IMAGE_DIRECTORY_ENTRY_TLS`) in `compiler/obj/coff.ax` and `compiler/link/pe.ax`, and emit `gs:[0x58]` TLS array lookups in `compiler/target/x64/isel.ax`.
- Maintain per-thread TLS instances in the MIR interpreter (`compiler/interp/interp.ax`) so spawned oracle threads each see isolated TLS storage.
- Provide `std/thread/local.ax` (`LocalKey<T>` with scoped `with` access and per-thread lazy init / cleanup on thread exit).

## Acceptance
- [ ] `tests/run/concurrency/tls/*.ax` (`modes: interp native`) verifies that `@thread_local` statics and `LocalKey<T>` are isolated per thread across multiple spawned threads and cleaned up on thread exit.
- [ ] `tests/ui/concurrency/tls/*.ax` verifies compile-time rejection of cross-thread sharing or escaping references to thread-local storage.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T413` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T413-report.md` with exact `## Files changed`.

## Out of scope
- ELF TLS models (`LocalExec`/`InitialExec`/`GeneralDynamic`, Phase 16 `E16.9`/`E16.2`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T413/build` and `python tools/axtest.py --compiler build-snap-T413/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-09 11:49:14 started (attempt 1) T413-impl
- 2026-11-09 13:14:45 requeue: user stopped (not charged: attempt refunded)
- 2026-11-09 13:32:56 started (attempt 1) T413-impl
- 2026-11-09 14:42:17 block: Missing compiler locks for PE TLS emission: linker.ax, encode.ax, frame.ax, pipeline.ax, code.ax
- 2026-11-09 14:55:09 unblocked (cycle 1) 
- 2026-11-09 14:59:11 started (attempt 1) T413-impl

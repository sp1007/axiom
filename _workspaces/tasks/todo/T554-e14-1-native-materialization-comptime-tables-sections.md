---
id: T554
title: E14.1 — Native materialization of lifted comptime aggregates, static tables & .rdata/.data/.bss emission
phase: P14-comptime-2-0-reflection-genera
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T552, T553]
priority: 174
status: todo
attempts: 0
paths: [compiler/lir, compiler/target/x64, compiler/obj, tests/run/comptime_native, tests/selfhost]
spec: [spec/SPEC-60-comptime-2-0.md, tasks/0509, tasks/0514]
covers: [REQ-CORE-2304, REQ-CORE-2305, REQ-CORE-2306, REQ-CORE-2307, REQ-CORE-2308, REQ-CORE-2309, REQ-CORE-2310, REQ-CORE-2311, REQ-CORE-2312, REQ-CORE-2313, REQ-CORE-2314, REQ-CORE-2315, REQ-CORE-2316, REQ-CORE-2317, REQ-CORE-2318, REQ-CORE-2319, REQ-CORE-2320, REQ-CORE-2321, REQ-CORE-2322, REQ-CORE-2323, REQ-CORE-2324, REQ-CORE-2325, REQ-CORE-2326, REQ-CORE-2327, REQ-CORE-2328, REQ-CORE-2329, REQ-CORE-2330, REQ-CORE-2331, REQ-CORE-2332, REQ-CORE-2333, REQ-CORE-2334, REQ-CORE-2335, REQ-CORE-2336, REQ-CORE-2337, REQ-CORE-2338, REQ-CORE-2339, REQ-CORE-2340, REQ-CORE-2341, REQ-CORE-2342, REQ-CORE-2343, REQ-CORE-2344, REQ-CORE-2345]
---
# T554 — E14.1 — Native materialization of lifted comptime aggregates, static tables & .rdata/.data/.bss emission

## Goal
Lower comptime-lifted aggregates, nested slices/views, and initialized `const`/`static` items into LIR data objects and COFF/PE `.rdata`, `.data`, and `.bss` sections without linking any comptime VM into runtime binaries.

## Scope
- Materialize comptime-computed structs, enums, arrays, and nested static slice views (`view<[T]>`, `Str`) into deterministic LIR global data objects with relocations for internal slice/view pointers in `compiler/lir` and `compiler/target/x64`.
- Emit read-only constants and immutable statics into `.rdata`, mutable initialized statics into `.data`, and zero-initialized statics into `.bss` in `compiler/obj`, preserving address identity for `static` items while permitting `const` deduplication (`AGLOBAL-109..145`).
- Verify that native executables produced from comptime-heavy programs contain zero comptime interpreter symbols or runtime VM overhead (`COMPTIME-24..25`).

## Acceptance
- [ ] Differential (`--interp` and native) tests in `tests/run/comptime_native` verify complex comptime-generated lookup tables, nested structs/enums/slices, `.rdata`/`.data`/`.bss` placement, and `static` address identity vs `const` value semantics.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`) with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T554-report.md` with exact `## Files changed`.

## Out of scope
- Reflection and `@derive` (`E14.2`, `T556`–`T560`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T554/build` and `python tools/axtest.py --compiler build-snap-T554/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:20:00 created by T214 (P14 phase planning)

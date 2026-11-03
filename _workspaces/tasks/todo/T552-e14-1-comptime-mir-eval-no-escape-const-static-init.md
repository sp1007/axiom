---
id: T552
title: E14.1 — Comptime MIR evaluator, resource no-escape barrier & deterministic const/static initialization
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T551]
priority: 172
status: todo
attempts: 0
paths: [compiler/interp, compiler/mir, tests/run/comptime, tests/mir/comptime]
spec: [spec/SPEC-60-comptime-2-0.md, 0102, 0140, tasks/0346, tasks/0509, tasks/0514]
covers: [REQ-CORE-713, REQ-CORE-714, REQ-CORE-715, REQ-CORE-716, REQ-CORE-717, REQ-CORE-718, REQ-CORE-719, REQ-CORE-720, REQ-CORE-721, REQ-CORE-722, REQ-CORE-723, REQ-CORE-724, REQ-CORE-725, REQ-CORE-726, REQ-CORE-727, REQ-CORE-728, REQ-CORE-729, REQ-CORE-2180, REQ-CORE-2181, REQ-CORE-2182, REQ-CORE-2183, REQ-CORE-2184, REQ-CORE-2185, REQ-CORE-2186, REQ-CORE-2187, REQ-CORE-2188, REQ-CORE-2189, REQ-CORE-2190, REQ-CORE-2191, REQ-CORE-2192, REQ-CORE-2193, REQ-CORE-2194, REQ-CORE-2195, REQ-CORE-2196, REQ-CORE-2197, REQ-CORE-2198, REQ-CORE-2199, REQ-CORE-2244, REQ-CORE-2245, REQ-CORE-2246, REQ-CORE-2247, REQ-CORE-2248, REQ-CORE-2249, REQ-CORE-2250, REQ-CORE-2251, REQ-CORE-2252, REQ-CORE-2253, REQ-CORE-2254, REQ-CORE-2255, REQ-CORE-2256, REQ-CORE-2257, REQ-CORE-2258, REQ-CORE-2259, REQ-CORE-2260, REQ-CORE-2261, REQ-CORE-2262, REQ-CORE-2263, REQ-CORE-2264, REQ-CORE-2265, REQ-CORE-2266, REQ-CORE-2267, REQ-CORE-2268, REQ-CORE-2269, REQ-CORE-2270, REQ-CORE-2271, REQ-CORE-2272, REQ-CORE-2273, REQ-CORE-2274, REQ-CORE-2275, REQ-CORE-2276, REQ-CORE-2277, REQ-CORE-2278, REQ-CORE-2279, REQ-CORE-2280, REQ-CORE-2281, REQ-CORE-2282, REQ-CORE-2283]
---
# T552 — E14.1 — Comptime MIR evaluator, resource no-escape barrier & deterministic const/static initialization

## Goal
Extend the MIR compile-time evaluator (`compiler/interp`) to execute full `comptime fn` and `comptime { ... }` bodies with compiler-managed heap allocations, deterministic `Drop` cleanup, strict value lifting (`AX_CTM_RESOURCE_ESCAPE`), and deterministic `const`/`static` initialization ordering.

## Scope
- Execute `comptime fn` and `comptime { ... }` blocks on Verified MIR in `compiler/interp`, supporting loops, closures, trait dispatch, transient comptime allocations (`Vec`, `String`, `Box`, `Arena`), and deterministic `Drop` execution before comptime completion (`ACOMP2-50..67`, `COMPTIME-51..57`).
- Implement the comptime-to-runtime value lifting barrier: deep-validate that the final returned value contains only liftable runtime representations (scalars, structs, enums, arrays, static slices/views) and reject any escaping comptime heap handle, live capability to a dead comptime owner, or raw comptime pointer with `AX_CTM_RESOURCE_ESCAPE`.
- Enforce deterministic `const` and `static` initialization dependency ordering, cycle detection (`AX_CTM_CYCLE`), step/memory budget diagnostics (`AX_CTM_STEP_LIMIT`, `AX_CTM_MEM_LIMIT`), and target-aware layout evaluation (`COMPTIME-70..72`, `AGLOBAL-49..86`).

## Acceptance
- [ ] Positive and negative tests in `tests/run/comptime` and `tests/mir/comptime` verify transient comptime heap allocation + deterministic `Drop`, value lifting of complex aggregates, rejection of escaping comptime resources (`AX_CTM_RESOURCE_ESCAPE`), and `const`/`static` cycle detection.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T552-report.md` with exact `## Files changed`.

## Out of scope
- Partial evaluation and specialization passes (`T553`) and native `.rdata`/`.data`/`.bss` emission (`T554`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T552/build` and `python tools/axtest.py --compiler build-snap-T552/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:20:00 created by T214 (P14 phase planning)

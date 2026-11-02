---
id: T555
title: E14.1 — Comptime 2.0, partial evaluation & const/static initialization conformance suite
phase: P14-comptime-2-0-reflection-genera
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T552, T553, T554]
priority: 175
status: todo
attempts: 0
paths: [tests/conformance/p14/e14_1_comptime]
spec: [spec/SPEC-60-comptime-2-0.md, 0102, 0140, tasks/0346, tasks/0509, tasks/0514]
covers: [REQ-CORE-755, REQ-CORE-756, REQ-CORE-757, REQ-CORE-758, REQ-CORE-759, REQ-CORE-760, REQ-CORE-761, REQ-CORE-762, REQ-CORE-763, REQ-CORE-2200, REQ-CORE-2201, REQ-CORE-2202, REQ-CORE-2203, REQ-CORE-2204, REQ-CORE-2205, REQ-CORE-2206, REQ-CORE-2207, REQ-CORE-2208, REQ-CORE-2209, REQ-CORE-2210, REQ-CORE-2211, REQ-CORE-2212, REQ-CORE-2213, REQ-CORE-2346, REQ-CORE-2347, REQ-CORE-2348, REQ-CORE-2349, REQ-CORE-2350, REQ-CORE-2351, REQ-CORE-2352, REQ-CORE-2353, REQ-CORE-2354, REQ-CORE-2355, REQ-CORE-2356, REQ-CORE-2357, REQ-CORE-2358, REQ-CORE-2359, REQ-CORE-2360]
---
# T555 — E14.1 — Comptime 2.0, partial evaluation & const/static initialization conformance suite

## Goal
Certify E14.1 exit criteria with an end-to-end differential and negative conformance suite covering `comptime fn`, `comptime` blocks, value lifting, resource no-escape, partial evaluation, specialization, and `const`/`static` initialization.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p14/e14_1_comptime` verifying:
  - `comptime fn` and `comptime { ... }` execution with ownership, capability, and deterministic `Drop` cleanup;
  - rejection of escaping comptime heap handles, capabilities, and raw pointers (`AX_CTM_RESOURCE_ESCAPE`) and undeclared external capabilities (`AX_CTM_CAPABILITY_DENIED`);
  - partial evaluation and specialization of `comptime` arguments and closures across `-O0` and `-O1`;
  - deterministic `const` vs `static` initialization, `.rdata`/`.data`/`.bss` materialization, and oracle/native agreement.

## Acceptance
- [ ] All positive and negative conformance tests in `tests/conformance/p14/e14_1_comptime` pass in both `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T555-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T555/build` and `python tools/axtest.py --compiler build-snap-T555/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:20:00 created by T214 (P14 phase planning)

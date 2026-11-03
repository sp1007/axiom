---
id: T553
title: E14.1 — Partial evaluation, comptime specialization & dependency-tracked caching
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T552]
priority: 173
status: todo
attempts: 0
paths: [compiler/opt, compiler/types/specialize.ax, compiler/driver, tests/mir/specialize, tests/run/specialize]
spec: [spec/SPEC-60-comptime-2-0.md, tasks/0346, tasks/0509, tasks/0514]
covers: [REQ-CTM-041, REQ-CTM-042, REQ-CORE-730, REQ-CORE-731, REQ-CORE-732, REQ-CORE-733, REQ-CORE-734, REQ-CORE-735, REQ-CORE-736, REQ-CORE-737, REQ-CORE-738, REQ-CORE-739, REQ-CORE-740, REQ-CORE-741, REQ-CORE-742, REQ-CORE-743, REQ-CORE-744, REQ-CORE-745, REQ-CORE-746, REQ-CORE-747, REQ-CORE-748, REQ-CORE-749, REQ-CORE-750, REQ-CORE-751, REQ-CORE-752, REQ-CORE-753, REQ-CORE-754, REQ-CORE-2284, REQ-CORE-2285, REQ-CORE-2286, REQ-CORE-2287, REQ-CORE-2288, REQ-CORE-2289, REQ-CORE-2290, REQ-CORE-2291, REQ-CORE-2292, REQ-CORE-2293, REQ-CORE-2294, REQ-CORE-2295, REQ-CORE-2296, REQ-CORE-2297, REQ-CORE-2298, REQ-CORE-2299, REQ-CORE-2300, REQ-CORE-2301, REQ-CORE-2302, REQ-CORE-2303]
---
# T553 — E14.1 — Partial evaluation, comptime specialization & dependency-tracked caching

## Goal
Implement MIR partial evaluation of `comptime` parameters and constant arguments, function/closure specialization, and deterministic dependency-tracked comptime evaluation caching.

## Scope
- Implement `compiler/types/specialize.ax` and MIR partial evaluation in `compiler/opt`: specialize functions instantiated with `comptime` parameters or constant closure environments, fold known branches (`if comptime`), and preserve runtime panic/overflow semantics on non-comptime paths (`ACOMP2-68..83`).
- Implement dependency-tracked comptime result caching in `compiler/driver`: fingerprint semantic inputs, target configuration, compiler version, and explicit external comptime inputs so cached comptime evaluations are 100% semantically equivalent to fresh execution (`ACOMP2-86..96`).
- Track global/static state effects and synchronization barriers across partial evaluation (`AGLOBAL-89..108`).

## Acceptance
- [ ] MIR golden tests in `tests/mir/specialize` and differential run tests in `tests/run/specialize` verify `comptime` parameter specialization, dead-branch elimination under `if comptime`, preservation of runtime traps on untaken paths, and cache invalidation when inputs change.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T553-report.md` with exact `## Files changed`.

## Out of scope
- Native `.rdata`/`.data`/`.bss` emission of lifted comptime tables (`T554`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T553/build` and `python tools/axtest.py --compiler build-snap-T553/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:20:00 created by T214 (P14 phase planning)

---
id: T716
title: E17.5 Compiler --profile=instrument pass, @profile/@no_profile hooks & source-mapped counter tables
phase: P17-debugging-runtime-introspectio
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T715]
priority: 187
status: todo
attempts: 0
paths: [compiler/instrument/profile, tests/selfhost/debug/profile]
spec: [spec/SPEC-96-profiler-performance-introspection.md, 0147, tasks/0572, tasks/0730, tasks/1056]
covers: [REQ-DBG-116, REQ-DBG-119]
---
# T716 — E17.5 Compiler --profile=instrument pass, @profile/@no_profile hooks & source-mapped counter tables

## Goal
Implement the compiler --profile=instrument pass, @profile / @no_profile attribute handling, and .axprof_desc source-mapped counter descriptor tables.

## Scope
- Implement `compiler/instrument/profile` running after semantic and ownership verification (`ADEBUG-82`): recognize `@profile` and `@no_profile` function attributes and `--profile=instrument` driver flags.
- Emit lightweight function entry/exit and loop-edge counter probes plus deterministic `.axprof_desc` metadata tables mapping each probe ID to its `SourceOrigin` span, function symbol, and inline call chain.
- Guarantee zero codegen changes and zero `.axprof_desc` overhead when `--profile` is not enabled.
- Add selfhost unit tests in `tests/selfhost/debug/profile`.

## Acceptance
- [ ] `axiomc build --profile=instrument` emits probe calls and `.axprof_desc` source-mapping tables; `@no_profile` functions are excluded from instrumentation.
- [ ] Builds without `--profile` produce byte-identical binaries to baseline builds.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T716-report.md` with exact `## Files changed`.

## Out of scope
- Runtime sampling engine and flamegraph/JSON exporters (`T717`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

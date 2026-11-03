---
id: T717
title: E17.5 std.profiler sampling engine, allocation/async contention telemetry & flamegraph/.axprof exporters
phase: P17-debugging-runtime-introspectio
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T712, T716]
priority: 188
status: todo
attempts: 0
paths: [std/profiler, compiler/driver/profile_cmd, tests/run/profiler]
spec: [spec/SPEC-96-profiler-performance-introspection.md, 0147, tasks/0572, tasks/0694, tasks/0730, tasks/1056]
covers: [REQ-DBG-116, REQ-DBG-119]
---
# T717 — E17.5 std.profiler sampling engine, allocation/async contention telemetry & flamegraph/.axprof exporters

## Goal
Implement the std.profiler runtime (sampling profiler, heap/arena allocation counters, async/mutex contention telemetry) and the axiomc profile CLI exporting .axprof, folded flamegraphs, and Chrome Trace JSON.

## Scope
- Implement `std.profiler` (`ProfileSession`, per-thread lock-free ring buffers with overflow tracking, timer/PMU stack sampling via `std.backtrace`, heap/arena allocation high-water hooks, and mutex/channel/async-task poll duration counters).
- Implement `compiler/driver/profile_cmd` (`axiomc profile`) combining `.axprof` / `.axprof_desc` telemetry with `compiler/debug/symbolicate` to attribute samples and counters across physical and inlined frames and export folded flamegraph stacks and Chrome Trace Event JSON.
- Add end-to-end profiling tests in `tests/run/profiler`.

## Acceptance
- [ ] Programs profiled with `std.profiler` / `axiomc profile` produce symbolicated `.axprof` files, folded flamegraph stacks, and Chrome Trace JSON with accurate hot-path, allocation, and contention attribution.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T717-report.md` with exact `## Files changed`.

## Out of scope
- Dynamic sanitizers (`E17.6`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

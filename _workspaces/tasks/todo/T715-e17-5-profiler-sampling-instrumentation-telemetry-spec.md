---
id: T715
title: E17.5 Canonical AXPROFILER sampling, instrumentation hooks, allocation/async counters & export specification (SPEC-96)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316, T711]
priority: 186
status: todo
attempts: 0
paths: [spec/SPEC-96-profiler-performance-introspection.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-95-debugger-contract-symbolication.md, 0147, tasks/0572, tasks/0694, tasks/0730, tasks/1056]
covers: [REQ-DBG-116, REQ-DBG-119]
---
# T715 — E17.5 Canonical AXPROFILER sampling, instrumentation hooks, allocation/async counters & export specification (SPEC-96)

## Goal
Consolidate the canonical specification for Axiom profiling (AXPROFILER), sampling & selective compiler instrumentation, allocation/async contention telemetry, and flamegraph/trace export into spec/SPEC-96-profiler-performance-introspection.md (AXS-PROF-* rules).

## Scope
- Write `spec/SPEC-96-profiler-performance-introspection.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-PROF-NNN` rules.
- Specify the zero-overhead-when-disabled observability contract (`0572 §313`, `0147 §20`) and non-interference with language semantics (`ADEBUG-86`).
- Specify the `AXPROFILER` sampling profiler (`tasks/0730 §476.1–13`, `tasks/1056 §11–25`): configurable frequency, per-thread lock-free sample ring buffers, explicit overflow counters (`1056 §16`), CPU vs wall-clock vs off-CPU wait attribution, and unwind-based call-stack sampling.
- Specify selective compiler instrumentation (`--profile=instrument`, `@profile`, `@no_profile` per `0730 §476.5–7`): static `.axprof_desc` probe descriptors mapping probe IDs to `SourceOrigin` and inline call sites.
- Specify allocation & arena high-water telemetry (`0730 §476.18–22`: allocation count, live/peak bytes, temporary lifetime attribution by call site) and concurrency/async contention telemetry (`0730 §476.14–17`: mutex/rwlock contention duration, channel wait, async task poll duration).
- Specify the `.axprof` binary profile format, folded flamegraph stack export, Chrome Trace Event JSON export, and `axiomc profile` CLI commands.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-96-profiler-performance-introspection.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-PROF-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T715-report.md` with exact `## Files changed`.

## Out of scope
- Compiler instrumentation pass and `std.profiler` runtime implementation (`T716`, `T717`, `T718`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

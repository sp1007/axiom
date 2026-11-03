---
id: T718
title: E17.5 AXPROFILER sampling, instrumentation, allocation/async telemetry & flamegraph conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T717]
priority: 189
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_5_profiler]
spec: [spec/SPEC-96-profiler-performance-introspection.md, 0147, tasks/0572, tasks/0694, tasks/0730, tasks/1056]
covers: [REQ-DBG-116, REQ-DBG-119]
---
# T718 — E17.5 AXPROFILER sampling, instrumentation, allocation/async telemetry & flamegraph conformance suite

## Goal
Certify the E17.5 exit criteria: zero disabled overhead, accurate sampling and instrumentation attribution across inlined frames, allocation/contention telemetry, and valid flamegraph/Chrome Trace exports.

## Scope
- Create `tests/conformance/p17/e17_5_profiler` covering:
-   - Zero-overhead verification when profiling is disabled (`0147 §20`, `0572 §313`).
-   - Sampling profiler and `--profile=instrument` exact call-count and hot-loop attribution, including inline-frame expansion (`0730 §476.9–10`) and `@no_profile` exclusion.
-   - Heap and `Arena` allocation profiling (`alloc_count`, `bytes_live`, `bytes_peak` per call site) and mutex/channel/async-executor contention telemetry.
-   - Folded flamegraph and Chrome Trace JSON schema and symbolication verification.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_5_profiler` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T718-report.md` with exact `## Files changed`.

## Out of scope
- Sanitizer conformance (`T722`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)

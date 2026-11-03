---
id: T625
title: E15.7 — Compiler pass-timing/code-size telemetry (--time-passes, --size-report) & benchmark harness enforcement
phase: P15-optimizer-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T622, T624, T628]
priority: 119
status: todo
attempts: 0
paths: [compiler/driver/perf_telemetry, tools/bench, tests/run/perf_contract, tests/selfhost]
locks: [tools/perf.py]
spec: [spec/SPEC-76-performance-contract.md, 0074, tasks/0408, tasks/0595, tasks/0706]
covers: [REQ-OPT-242, REQ-OPT-243, REQ-OPT-244, REQ-OPT-245]
---
# T625 — E15.7 — Compiler pass-timing/code-size telemetry (--time-passes, --size-report) & benchmark harness enforcement

## Goal
Implement structured `--time-passes` and `--size-report` telemetry in `compiler/driver/perf_telemetry` and extend `tools/perf.py` + `tools/bench` with the canonical P15 benchmark suite and compile-time/code-size budget enforcement per `spec/SPEC-76-performance-contract.md`.

## Scope
- Implement `--time-passes` (per-stage and per-optimization-pass elapsed time, peak arena/heap bytes, instruction/block counts) and `--size-report` (per-section `.text`/`.rdata`/`.data`/`.bss` and per-symbol byte breakdown) in `compiler/driver/perf_telemetry`, ensuring normal reproducible build outputs remain completely unaffected by wall-clock timing (`REQ-OPT-242..245`).
- Populate `tools/bench` with canonical Axiom micro- and macro-benchmarks (scalar/loop kernels, iterator pipelines, allocation promotion, devirtualization, SIMD auto-vectorized kernels, and `axiomc` self-compile throughput).
- Update `tools/perf.py` to compare `-O0`, `-O1`, `-O2`, and `-Oz` against the `SPEC-76` compile-time, runtime speedup, and code-size budgets and emit machine-readable JSON reports for CI regression tracking.

## Acceptance
- [ ] Run tests in `tests/run/perf_contract` verify `--time-passes`, `--size-report`, and `python tools/perf.py --check-budgets` across the `tools/bench` suite, confirming `-O2` speedup and `-Oz` size reduction targets without changing binary reproducibility.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T625-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated phases; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T625/build` and `python tools/axtest.py --compiler build-snap-T625/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:44:00 created by T215 (P15 phase planning)

---
id: T494a
title: Test hygiene — single-shot wall-clock ratio perf tests (`perf/build_scaling`, `perf/own_scaling`) flake under concurrent load; use min-of-3 per size
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T494]
priority: 46
status: done
attempts: 1
paths: [tests/perf/build_scaling/build_scaling.py, tests/perf/own_scaling/own_scaling.py, tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py, tests/perf/build_scaling/build_scaling.test, tests/perf/build_scaling/build_scaling_o1.test, tests/perf/own_scaling/own_scaling.test, tests/perf/own_scaling/own_wave2_subtimers_and_scaling.test]
locks: []
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md]
covers: [REQ-TST-072]
started: 2026-11-22 16:46:37
finished: 2026-11-22 17:39:38
---
# T494a — Robust scaling ratios

## Goal
`perf/build_scaling/build_scaling_o1.test` failed the Tier-1 sweep of fullrun-3 with `ratio 5.08 limit 5.00` (passes 3/3 in
isolation, parity in A/B), and `perf/own_scaling` did the same in fullrun-2 (`_workspaces/reports/fullrun-3.md` §4). The
scripts time each input size once (`--time-passes` sub-timers of one compile) and compare `t(4N) / t(N)`; one disturbed
sample on the shared 4-core host decides the result.

## Scope
- Each size is compiled 3 times (sequentially) and the **minimum** of each timer is used (minimum is the estimator least
  affected by contention; the median is printed too for diagnosis). Same limits, same floors (`max(t, 0.05)`); a real
  regression (every sample over the limit) still fails.
- Print all samples on stderr so a failure is diagnosable from the log; keep the `stdout-contains` contract.
- Raise `timeout:` in the `.test` files only as much as the extra runs need (report old/new wall time per test).
- Self-check: run each test 10 times while another `-j 2` suite runs (e.g. `tests/run` subset) and report pass counts;
  demonstrate a true regression still fails (e.g. a `--limit 1.0` run).

## Acceptance
- [ ] 10/10 passes under load for each changed test; the forced-limit run fails; wall times reported.
- [ ] `tests/perf` passes; gate per axiom-qa.md "Per-task gate scope".
- [ ] Report `_workspaces/reports/T494a-report.md` with exact `## Files changed`.

## Out of scope
- Changing limits or the compiler; other perf tests unless they use the same single-shot pattern (list them in the report).

## Log
- 2026-11-22 created by axiom-architect (triage-1122; fullrun-3 §4 follow-up, fullrun-2 own_scaling)
- 2026-11-22 16:27:36 started (attempt 1) T494a-impl
- 2026-11-22 16:45:57 requeue: restart (not charged: attempt refunded)
- 2026-11-22 16:46:37 started (attempt 1) t494a-impl
- 2026-11-22 17:39:38 accepted by QA -> done

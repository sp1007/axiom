---
id: T423g
title: Test hygiene — `tests/smoke.list` has no pool for the `tools` and `build_native` groups (`axtest.py --smoke --check` fails); make the gate report it
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T423f]
priority: 45
status: todo
attempts: 0
paths: [tests/smoke.list, tools/taskgate.py, tests/tools/taskgate_smoke_check]
locks: []
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md]
covers: [REQ-TST-072]
---
# T423g — Smoke pools for every top-level group

## Goal
`python tools/axtest.py --smoke --check` reports `SMOKE-CHECK PROBLEM group build_native has no pool entry` and
`... group tools has no pool entry` (`FAILED (2 problem(s))`, verified at HEAD in triage-1122;
`_workspaces/reports/T423f-report.md` / `T423f-qa.md` follow-ups). The per-task gate therefore never draws from these groups,
and nothing flagged the gap when T423f added `tests/tools/`.

## Scope
- Add `pool tools: tools/build_axiomc_fallback/seed_works.test` (60 s timeout, cache-inputs declared) or a lighter id of
  that group, and a light `pool build_native: …` id (pick by the recorded durations; both existing ids have a 120 s timeout,
  so check the worst-case draw still fits the bound printed by `--check`).
- `tools/taskgate.py`: run `axtest.py --smoke --check` as part of the gate and print its result; a change set that adds a new
  top-level `tests/<group>/` without a pool entry fails the gate with a clear message (other existing problems are printed
  but do not fail an unrelated task). Self-test under `tests/tools/taskgate_smoke_check/` with a fake tree.

## Acceptance
- [ ] `python tools/axtest.py --smoke --check` prints `SMOKE-CHECK OK` (or the tool's success line) at the task's tree.
- [ ] The taskgate self-test shows the new-group failure and the pass case; `tests/tools` passes.
- [ ] Report `_workspaces/reports/T423g-report.md` with exact `## Files changed`.

## Out of scope
- Changing the smoke draw algorithm; `spec/`, `docs/`.

## Log
- 2026-11-22 created by axiom-architect (triage-1122; T423f report/QA follow-up)

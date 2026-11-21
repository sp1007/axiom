---
id: T423f
title: Tooling — `build_axiomc.py` seeded bootstrap falls back to the full chain when the seed cannot compile the new sources
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 35
status: todo
attempts: 0
timeout_min: 240
paths: [tests/tools/build_axiomc_fallback]
locks: [tools/build_axiomc.py]
spec: [spec/decisions/ADR-0046-t423-fiber-followups-and-tracked-xfail.md]
covers: [REQ-TST-072]
---
# T423f — Seeded bootstrap fallback

## Goal
T423 report F5: when the cached seed compiler cannot type-check the new compiler/std sources (T423 added `host.fiber_*`
declarations unknown to the old typeck), `python tools/build_axiomc.py --out <dir>` fails hard (`bootstrap: FAIL seeded A`) and
a human/agent must rerun with `--full-chain` (~8 minutes). Every change that adds a host intrinsic or new syntax hits this.

## Scope
- In `tools/build_axiomc.py` (seeded mode chosen by `auto`, not when the user passed an explicit `--seed`): when stage
  "seeded A" fails to compile, print one clear line (`bootstrap: seeded A failed, falling back to full chain`) and run the full
  `axiom0 -> c1 -> c2 (-> c3)` chain in the same invocation; the resulting compiler becomes the new cached seed as today. An
  explicit `--seed <path>` keeps failing hard (the user asked for that seed). The B == C fixed-point check and the stage-0
  smoke parity guard are unchanged.
- Tests `tests/tools/build_axiomc_fallback/*` (python `cmd:` tests with a fake/stub seed so they run in seconds): auto seed that
  fails → fallback runs the full chain (stubbed) and reports it; explicit seed that fails → exit non-zero; seed that works → no
  fallback.

## Acceptance
- [ ] New tests pass; `python tools/build_axiomc.py --out <tmp>` works from a stale seed in the snapshot (log in the report).
- [ ] Gate per axiom-qa.md "Per-task gate scope".
- [ ] Report `_workspaces/reports/T423f-report.md` with exact `## Files changed`.

## Out of scope
- Changing the cache layout or seed selection policy, `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-21 created by axiom-architect (triage-t423; T423 QA follow-up 5 / report F5)

---
id: T436
title: Baseline fix — selfhost driver bundles (commands_b, inspect_diff_b) and stage-1 parity oracle
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452]
priority: 15
status: todo
attempts: 0
timeout_min: 900
paths: [tests/selfhost/driver, tests/selfhost/stage1]
locks: [tests/selfhost, compiler/driver, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-20-selfhost.md, spec/SPEC-00-bootstrap.md]
covers: [REQ-BOOT-085, REQ-BLD-030, REQ-TST-089]
---
# T436 — Baseline fix: selfhost driver bundles and stage-1 parity

## Goal
`selfhost/driver/qa_driver_commands_b.ax`, `selfhost/driver/qa_driver_inspect_diff_b.ax` and
`selfhost/stage1/stage1_bootstrap.test` pass again under `axiomc2`.

## Scope
- Diagnose each failure at HEAD (they fail without any running task's change set). `stage1_bootstrap.test` runs
  `stage1_oracle.py` and expects `STAGE1-PARITY OK`; it exits 1 with empty stderr: first make the oracle print the
  failing step and the differing output (a silent exit 1 is itself a defect), then fix the cause.
- For the driver `_b` bundles: find which case differs (bundle exit code encodes pass/case), decide whether the bundle
  generator (`gen_driver_tests.py`) is stale relative to `compiler/driver` or the driver regressed; fix at the root.
  A fix in `compiler/driver` is allowed (locked here); a root cause elsewhere in `compiler/` is reported for a split.
- Regenerate with their generators every bundle embedding an edited module; remove the T436 lines from the baseline.

## Acceptance
- [ ] The 3 ids pass under `axiomc2.exe` built in `build-snap-T436` (all modes of each id).
- [ ] `stage1_oracle.py` reports the failing step and a diff on failure (shown in the report by a temporary mutation).
- [ ] Complete suite: failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0;
  every `tests/selfhost/**/bundles_current.test` passes.
- [ ] The T436 lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T436-report.md` with exact `## Files changed`.

## Out of scope
- `bootstrap/axiom0` (frozen at `axiom0-frozen`). `docs/`. Other `tests/selfhost` groups except regeneration.

## Notes
- Build/test in `build-snap-T436` with `tools/build_axiomc.py` and `tools/axtest.py --exclude-requires axiom0-internal`.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)

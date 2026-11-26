---
id: T546
title: Baseline fix — selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test asserts that `_workspaces/baseline-failures.txt` is empty
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 20
status: done
attempts: 1
paths: [tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py]
locks: [_workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-072]
started: 2026-11-26 23:59:12
finished: 2026-11-27 01:02:47
---
# T546 — The T442 boundary oracle no longer reads the baseline file

## Why
Found by the T544 gate (`_workspaces/reports/T544-qa.md` "Pre-existing failures (not in baseline)") and triaged in
`_workspaces/reports/triage-2026-11-26-preexisting.md`. The function
`check_baseline_and_temp_cleanup` of `qa_t442_obj_link_driver_bounds_oracle.py` (~line 210) fails with "`_workspaces/baseline-failures.txt` still has active lines"
whenever the baseline has any entry. The baseline is a living gate list (ADR-0041): it is non-empty by design while fix
tasks are open, and its content is board state, not a property of the obj_link_driver bundles. The check was a
one-time T442 acceptance item ("T442 removed its own baseline lines") frozen into a permanent test; it now fails on
every HEAD with a non-empty baseline, independent of any compiler change.

## Scope
1. Remove the baseline-file check from `check_baseline_and_temp_cleanup` (rename it, e.g. `check_temp_cleanup`); keep
   the leftover-artifact check (`build/tmp_obj_link_driver_*`, `_gen_ref*`) unchanged. Update the module docstring
   item 4 accordingly. Do not replace it with a narrower baseline check (e.g. "no obj_link_driver ids in the baseline"):
   the gate rule already enforces that a failing id is listed, and a test must not depend on `_workspaces/`.
2. Remove this task's line from `_workspaces/baseline-failures.txt` (and its comment header if it becomes empty).
3. No other check, bundle, generator or the `.test` file changes; the stdout marker stays
   `T442-BOUNDS ok bundles=8 smoke_blobs=19 diff_blobs=55 main42_obj=336 main42_exe=2048`.

## Acceptance
- [ ] `grep -n "baseline" tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py` finds nothing.
- [ ] `selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test` passes with the current (non-empty) baseline.
- [ ] Gate: task test + `selfhost/obj_link_driver` group + smoke; failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T546-report.md` with an exact `## Files changed`.

## Out of scope
- Any compiler, generator or bundle change.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/triage-2026-11-26-preexisting.md`)
- 2026-11-26 23:59:12 started (attempt 1) T546-impl
- 2026-11-27 01:02:47 accepted by QA -> done

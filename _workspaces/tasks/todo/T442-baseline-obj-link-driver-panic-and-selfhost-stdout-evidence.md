---
id: T442
title: Baseline fix — selfhost obj_link_driver bundles panic (exit 101); `// stdout:` native evidence in driver and obj_link_driver generators
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452, T436]
priority: 18
status: todo
attempts: 0
timeout_min: 900
paths: [tests/selfhost/obj_link_driver, tests/selfhost/driver/gen_driver_tests.py, tests/selfhost/driver/qa_driver_commands_a.ax, tests/selfhost/driver/qa_driver_commands_b.ax, tests/selfhost/driver/qa_driver_inspect_diff_a.ax, tests/selfhost/driver/qa_driver_inspect_diff_b.ax]
locks: [tests/selfhost, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-095, REQ-TST-046]
---
# T442 — Baseline fix: obj_link_driver bundles and native evidence of the driver bundles

## Goal
`selfhost/obj_link_driver/qa_obj_link_driver_diff.ax` and `qa_obj_link_driver_smoke.ax` pass, and every bundle of
`selfhost/driver` and `selfhost/obj_link_driver` proves its native legs with an exact `// stdout:` line
(WEAK-NATIVE 0) (ADR-0042 §1, T452 report "WEAK-NATIVE finding").

## Scope
- Observed (T452 report/QA, identical at HEAD): both obj_link_driver bundles exit 101 (panic) in native/native-O1.
  Diagnose the panic (message, failing case); fix it in the generator/bundle cases if the defect is in the test; a
  defect in `compiler/obj_link_driver`, `compiler/link`, `compiler/obj` or `compiler/driver` is reported with a
  minimal repro for a split and the ids stay on the baseline under the new task.
- Generators `tests/selfhost/driver/gen_driver_tests.py` and `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py`:
  each bundle's `main` prints one final line `OK <bundle name>` after all cases pass, and the header declares
  `// stdout: OK <bundle name>\n` (the pattern used by `selfhost/opt/qa_opt_pipeline.ax`). Regenerate the 6 bundles
  with their generators only.
- Remove the two `T442` lines from `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] Both obj_link_driver ids pass in all modes in `build-snap-T442`; the 4 driver bundles keep their T436 result.
- [ ] `axtest -v selfhost/driver selfhost/obj_link_driver`: WEAK-NATIVE 0 (was 12).
- [ ] Mutation proof: changing the expected `OK` text in one regenerated bundle header makes its native legs FAIL.
- [ ] `selfhost/driver/bundles_current.test` and `selfhost/obj_link_driver/bundles_current.test` pass.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline after the removals.
- [ ] Report `_workspaces/reports/T442-report.md` with exact `## Files changed`.

## Out of scope
- `compiler/` edits (become a split), `bootstrap/axiom0`, `docs/`.

## Notes
- Depends on T436, which owns `tests/selfhost/driver` and fixes the driver `_b` bundles first.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §1, architect inbox 1)

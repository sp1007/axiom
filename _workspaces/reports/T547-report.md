# T547 report — stage-1 parity oracle skips post-freeze features

## Summary
`stage1_oracle.py` step 2 (`step2:check-json`) now treats a sampled UI file on which the frozen axiom0 reports any
`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` diagnostic as outside the frozen bootstrap subset: the file is skipped for parity and
the next matching file of the same pattern is taken, so every pattern still contributes up to 3 compared files. The
criterion is axiom0's own diagnostic (parsed from `check --json`); there is no exclusion list and no file name in the
oracle. Skipped files are printed as `STAGE1-PARITY skipped-post-freeze: <rel>`. If a pattern has at least one non-helper
file but ends with 0 compared files, step 2 fails (`FAIL [step2:check-json]: every candidate of N pattern(s) was skipped ...`).
`STAGE1-PARITY OK json_checked=.. run_checked=..` is unchanged. Only the UI diagnostic patterns are filtered; the run
parity sample (`RUN_PARITY_PATTERNS`) is not.

## Changes
- `stage0_reports_post_freeze(result)` (new, pure, unit-testable): True when stage-0 JSON output contains the code.
  Unparsable or empty output is not skipped (it still goes to the comparison, which fails as before).
- `collect_sample(root, patterns, per_pattern=3, accept=None, skipped=None, starved=None)`: optional filter with refill.
  Without a filter, behaviour is identical to before.
- `qa_stage1_oracle_diff_diag.py`: new `test_post_freeze_skip_rule` (stage-0 `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` skipped;
  `AX_TYPE_MISMATCH`, clean output and non-JSON output are not skipped; a mixed diagnostic list is skipped; refill picks the
  next file; skipped and starved lists are reported; unfiltered behaviour unchanged).
- `_workspaces/baseline-failures.txt`: removed T547's entry together with its comment block (the block belonged only to it).

## Evidence (all in snapshot `build-snap-T547`, Release, clang; axiomc2 built with `tools/build_axiomc.py`, fixed point OK)
- Oracle run to the end (steps 1-4), `python tests/selfhost/stage1/stage1_oracle.py build/axiomc2.exe <tmp> .`:
  `STAGE1-PARITY skipped-post-freeze: tests/ui/typeck/bug_float_unsupported.ax` then
  `STAGE1-PARITY OK json_checked=24 run_checked=12`, exit 0. Steps 3-4 (obj/exe/runtime parity, axtest slices with
  0 WEAK-NATIVE) therefore pass; no later-step failure exists, nothing to report as BLOCKED.
- Compared `tests/ui/typeck` files after the skip: `assign_mismatch.ax`, `bug_literal_out_of_range.ax`, `bug_main_params.ax`
  (3 files). Only `bug_float_unsupported.ax` is skipped across all patterns; no pattern is starved.
- `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 selfhost/stage1`:
  `TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0` (`stage1_bootstrap.test`, `qa_stage1_oracle_diff_diag.test`).
- Mutation (in the snapshot only, in-process, nothing committed): wrapped `run_cmd` so axiomc1's `check --json` on the
  compared file `tests/ui/typeck/assign_mismatch.ax` reports code `AX_MUTATED_CODE`; `main()` returned 1 with
  `FAIL [step2:check-json]: check --json mismatch on tests/ui/typeck/assign_mismatch.ax` and the diff
  `-AX_TYPE_MISMATCH / +AX_MUTATED_CODE`. A non-post-freeze mismatch therefore still fails.
- Gate: `python tools/taskgate.py --task T547 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --extra selfhost/stage1/qa_stage1_oracle_diff_diag.test`
  (with the baseline entry removed): `TOTAL 57 PASS 57 FAIL 0`, failing ids: none, archcheck clean (252 files, 0 violations),
  BASELINE OK, own/changed tests 0 WEAK-NATIVE (the 3 WEAK-NATIVE in the run belong to unrelated smoke tests), 34 smoke ids
  across every group, wall time 627 s. Log: `_workspaces/T547_taskgate.log`.
- `bootstrap/axiom0` and `tests/ui/typeck/bug_float_unsupported.ax`: unchanged (`git status` clean for both).

## Decisions
- The filter applies to the UI diagnostic sample only; the run-parity sample also feeds steps 3-4, where dropping a file would
  silently shrink the native comparison, and it has no post-freeze file today.
- Unparsable stage-0 output is deliberately not treated as post-freeze, so a crash still fails the step.
- `qa_stage1_oracle_diff_diag.py` is under `locks:` only, so `taskctl snapshot` did not copy it; I copied it into the
  snapshot by hand for testing.
- Scratch test directories created by my diff-diag test and mutation run live under `build-snap-T547/_workspaces/` and
  are not part of the change set.

## Files changed
- tests/selfhost/stage1/stage1_oracle.py
- tests/selfhost/stage1/qa_stage1_oracle_diff_diag.py
- _workspaces/baseline-failures.txt

STATUS: COMPLETE round=0

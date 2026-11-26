---
id: T547
title: Baseline fix — selfhost/stage1/stage1_bootstrap.test compares axiom0 and axiomc on a float UI test (bug_float_unsupported.ax) that SPEC-41 says must diverge
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 20
status: done
attempts: 1
timeout_min: 300
paths: [tests/selfhost/stage1/stage1_oracle.py]
locks: [tests/selfhost/stage1/qa_stage1_oracle_diff_diag.py, _workspaces/baseline-failures.txt]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-20-selfhost.md, spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md]
covers: [REQ-TST-089]
started: 2026-11-27 01:03:13
finished: 2026-11-27 02:26:04
---
# T547 — The stage-1 parity oracle compares only the frozen axiom0 language subset

## Why
Found by the T544 gate (`_workspaces/reports/T544-qa.md` "Pre-existing failures (not in baseline)") and triaged in
`_workspaces/reports/triage-2026-11-26-preexisting.md`. `stage1_oracle.py` step `step2:check-json` takes the first 3
non-helper files of each `UI_DIAG_PATTERNS` glob and requires byte-identical canonical `check --json` from `axiom0` and
`axiomc1`. T457 (5ee8652a, 2026-11-24) enabled `f32`/`f64` in axiomc and rewrote
`tests/ui/typeck/bug_float_unsupported.ax` to expect one `AX_TYPE_MISMATCH` (SPEC-41 AXS-FLT-035 rule 1). axiom0 is
frozen (after T087) and keeps rejecting floats with three `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, exactly as SPEC-41
AXS-FLT-001 rule 2 requires. Both compilers are right; the oracle's premise "every sampled UI file has stage-0 parity"
stopped holding when the first post-freeze feature landed. The architect's run of the whole sample (24 files) with
`build/axiom0.exe` vs the HEAD-built `axiomc2_O1_c8d9621632f121f5.exe` shows this is the only divergent file today.

## Scope
1. In `stage1_oracle.py` step 2, a sampled file on which **axiom0** reports any `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`
   diagnostic is outside the frozen bootstrap subset: skip it for parity and take the next matching file of the same
   pattern, so each pattern still contributes up to 3 compared files (`collect_sample` gets a filter, or step 2 refills).
   Use axiom0's own diagnostic as the criterion — no hand-maintained exclusion list, no file names in the oracle.
2. Print the skipped files (`STAGE1-PARITY skipped-post-freeze: <rel>`) so the evidence stays visible; the success
   marker `STAGE1-PARITY OK` is unchanged.
3. Guard against the filter hiding everything: fail `step2:check-json` if a pattern that has ≥ 1 non-helper file ends
   with 0 compared files.
4. If `qa_stage1_oracle_diff_diag.py` (it imports `stage1_oracle`) needs an update for the new helper signature, adapt
   it; add a small case there for the skip rule (fake stage0 output with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` is skipped,
   any other mismatch still fails).
5. Run `stage1_bootstrap.test` to the end (steps 3–4 never ran while step 2 failed). A later-step failure that is not
   caused by the oracle is reported with evidence (`STATUS: BLOCKED` with the list) — not patched here.
6. Remove this task's line from `_workspaces/baseline-failures.txt`.

## Acceptance
- [ ] `selfhost/stage1/stage1_bootstrap.test` and `selfhost/stage1/qa_stage1_oracle_diff_diag.test` pass; the log shows
      `skipped-post-freeze: tests/ui/typeck/bug_float_unsupported.ax` and still 3 compared `tests/ui/typeck` files.
- [ ] Mutation: change one expected diagnostic of a compared (non-skipped) file in a scratch copy → step 2 fails.
- [ ] `bootstrap/axiom0` and `tests/ui/typeck/bug_float_unsupported.ax` are unchanged.
- [ ] Gate: task tests + `selfhost/stage1` group + smoke; failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T547-report.md` with an exact `## Files changed`.

## Out of scope
- Any axiom0 change (frozen) or typeck change: both compilers behave as SPEC-41 specifies.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/triage-2026-11-26-preexisting.md`)
- 2026-11-27 01:03:13 started (attempt 1) T547-impl
- 2026-11-27 02:26:04 accepted by QA -> done

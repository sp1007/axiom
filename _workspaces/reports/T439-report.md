# T439 — Baseline fix: gatecheck self-test `test_check_without_command_blocks`

## Summary
`python tools/tests/gatecheck/run_selftests.py` now reports `SELFTEST 34 tests, 0 failures, 0 errors`
(33 before + 1 added). The baseline entry for the formerly failing id is removed.

## Diagnosis (root cause)
- Failing run: `AssertionError: 'check differential has no command yet' not found in 'MS-P1 BLOCKED: check differential
  exited 1: TypeError: expected str, bytes or os.PathLike object, not NoneType'`.
- `tools/gatecheck.py` is correct. T029 (commit 91da06ec) legitimately gave the `differential` check a command
  (`CHECK_COMMANDS["differential"] = ["python", "tools/axtest.py", "diff"]`, and `determinism` -> `bash tools/ci.sh`);
  its header comment ("until then a due milestone listing them is BLOCKED with 'no command'") is the historic state.
- The self-test (T022) used `differential` as its example of "a check without a command", so after T029 the check
  actually ran `tools/axtest.py diff` against the fixture's stub axtest (which has no `--root`, so it crashed with the
  `TypeError` and the milestone was BLOCKED for a different reason). The R9 behaviour (BLOCKED, never PASS) was intact;
  the test was stale. No gatecheck change needed.
- Today the only table entry with no command is the internal `gatecheck` check, which never reaches `run_check`, and
  unknown check names are rejected earlier (`gatecheck.py:283`). So the "no command" branch of `run_check` is
  unreachable through the CLI and can only be exercised by patching the table in-process.

## Fix (smallest change, intent kept)
`tools/tests/gatecheck/test_gatecheck.py` only:
- `test_check_without_command_blocks` now loads `gatecheck.py` as a module, sets `CHECK_COMMANDS["differential"] = None`
  in that module copy, runs `main(["--root", ..., "--gate", "T022"])` and asserts rc 1 and the exact output
  `MS-P1 BLOCKED: check differential has no command yet (AXS-BOOT-050)` (the BLOCKED outcome, explicitly).
- New `test_differential_check_runs_axtest_diff`: with a stub `tools/axtest.py` answering `diff`, exit 0 -> `MS-P1 PASS`;
  exit 3 -> `MS-P1 BLOCKED: check differential exited 3: diff mismatch`. Covers the real T029 table entry that the
  old test accidentally depended on.
- `_workspaces/baseline-failures.txt`: removed the T439 entry and its now-empty `# --- T439 ... ---` header (no other
  line touched).

## Evidence
- `python tools/tests/gatecheck/run_selftests.py` -> `SELFTEST 34 tests, 0 failures, 0 errors` (before: 33 tests, 1 failure).
- `python tools/tests/taskgate/run_selftests.py` -> `SELFTEST 44 tests, 0 failures, 0 errors`.
- `python tools/tests/axtest/run_selftests.py` -> first run `138 tests, 1 failures` (failing test not captured: only the
  tail was kept; it ran while other agents were editing the working-tree files `tools/axtest_cache.py` and
  `tools/axtest_affected.py`, which are not part of this task); two further full runs -> `138 tests, 0 failures, 0 errors`.
  Reported as a possible flake or a transient effect of concurrent edits; not attributable to this change (it touches
  neither axtest nor taskgate).
- Not run (resource instruction: self-tests only): `tools/taskgate.py --task T439` with the smoke/affected suites; the
  QA gate runs it and should see `tools/tests/gatecheck` PASS and no KNOWN entry.

## Follow-ups
- The comment above `CHECK_COMMANDS` in `tools/gatecheck.py` still says `differential`/`determinism` have no command
  "until T029"; harmless, left as is (comment-only, outside the minimal fix).
- Possible flake in `tools/tests/axtest` self-test under concurrent working-tree edits (one occurrence, not reproduced).

## Files changed
- tools/tests/gatecheck/test_gatecheck.py
- _workspaces/baseline-failures.txt
- _workspaces/reports/T439-report.md

STATUS: COMPLETE round=0

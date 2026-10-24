---
id: T139
title: axtest cross-mode agreement and native-evidence report for run tests
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T134, T140]
priority: 100
status: doing
attempts: 1
paths: [tools/tests/axtest, tests/lir, tests/hir]
locks: [tools/axtest.py, tests/README.md]
spec: [spec/ROADMAP.md, tasks/0361, tasks/0480]
covers: [REQ-TST-046, REQ-TST-107]
started: 2026-10-25 04:09:11
agent: T139-impl
---
# T139 — axtest cross-mode agreement and native-evidence report for run tests

## Goal
The runner itself enforces the standing rule recorded after T134 (axiom-testing §Differential
testing, axiom-qa Gate protocol 4a): *interp correct does not imply native correct; a native PASS
must be proven to check something.* Today `tools/axtest.py` judges every mode of a `run` test
separately against the directives; a run test that prints without a `stdout:` directive, or whose
only expectation is exit 0, passes in native mode even when native computes something different
from the interpreter. Only `test: diff` compares executors with each other.

## Scope
- **Cross-mode agreement for run tests:** when a `run` test executes in two or more of
  interp / native-O0 / native-O1 in one runner invocation, the runner also compares the observed
  exit code and stdout bytes of every native variant with the interp variant (as `run_diff` does).
  A disagreement makes the native entry FAIL with `interp/native disagree` and the byte diff
  (`byte_diff`). Per-mode judging against the directives is unchanged. Implementation (caching the
  interp observation, ordering of entries, `--filter` interplay) is the engineer's choice (TYPE A).
  Tests that legitimately differ by mode (interp-limit exit 124, `modes:` restricted tests, SKIP of
  one leg) are not compared; no new directive is added for exemptions.
- **Native-evidence report:** `--json` gains, per run/diff entry, a boolean `weak_native_evidence`
  (native leg executed, expected exit 0, no `stdout`/`stderr`/`stdout-contains`/`stderr-contains`
  directive, and not `test: diff`), and the text output prints at the end
  `WEAK-NATIVE n` with `--verbose` listing the names. It is informational (does not change the exit
  status); QA uses it in Gate protocol 4a.
- Runner self-tests in `tools/tests/axtest` (stub compiler `stubcc.py`): agreement PASS, stdout
  disagreement FAIL, exit-code disagreement FAIL, interp-limit test not compared, weak-evidence flag
  set/unset.
- **Golden comparison for inspect manifests (audit OI-10, ADR-0034 §3):** one new manifest
  directive `stdout-file: <path>` (path relative to the manifest): the step's stdout is compared
  byte-for-byte with that file, and `--bless` rewrites it. The 31 `tests/lir/*.test` manifests and
  `tests/hir/more.test` gain it for their sibling golden (`.lir` / `.hir`); `tests/hir/more.test`
  and any of these manifests that call `{build}/axiom0` use `{compiler}`. The goldens that differ
  from current output (audit: `abi_arg`, `abi_result`, `call`, `offset`, `qa_multi_branch`, plus any
  found) are reviewed one by one: a legitimate representation change is re-blessed with the reason
  in the report; a lowering bug is a `## Follow-ups` entry (the golden stays, the test is
  `xfail: <fix task>` once the architect files it). Orphaned goldens with no manifest get one or are
  deleted with a reason. `tests/lir/COVERAGE.md` is corrected to state that these goldens are
  self-snapshot (category C) evidence.
- **Leg isolation (T141 QA round 2 N1, ADR-0036 §6):** the legs (interp, native-O0, native-O1) of one
  test file never run concurrently: they are scheduled in one worker, in a fixed order (this also
  serves the agreement check). Today every leg runs with `cwd=self.root`, so legs of
  `tests/run/host/fs/dir.ax` (fixed relative directory `test_host_dir`) race under `-j > 1`.
- `tests/README.md`: document the agreement check, leg serialisation, `WEAK-NATIVE` and `stdout-file:`.

## Acceptance
- [ ] `python tools/tests/axtest/run_selftests.py` passes, including the new cases above.
- [ ] Full suite in the snapshot `build-snap-T139`
      (`python tools/axtest.py --compiler build/axiom0.exe`) passes with the agreement check on; every
      test that newly fails is a real interp/native divergence and is listed in the report's
      `## Follow-ups` (test, both observations, diagnosis) — the task does not edit tests (other than the
      `tests/lir`/`tests/hir` golden work above) or compiler code to make it pass; the architect files the fix tasks.
- [ ] The report states the `WEAK-NATIVE` count and the list of weak tests (T145 drives it to 0 in
      the T086 directories).
- [ ] Runner self-tests cover `stdout-file:` (match PASS, mismatch FAIL with byte diff, `--bless`
      rewrites); every `tests/lir/*.test` and `tests/hir/more.test` compares its golden; the report
      lists each drifted golden with its verdict (re-blessed + reason, or follow-up).
- [ ] The final line format `TOTAL n PASS p FAIL f SKIP s XFAIL x` is unchanged (the WEAK-NATIVE
      line comes before it).
- [ ] Runner self-test: two legs of one stub test that create and remove the same relative directory
      never overlap under `-j 8`; `python tools/axtest.py --compiler build/axiom0.exe -j 8 --filter
      run/host/fs` passes 20 consecutive times (log in the report).
- [ ] Python 3 standard library only.
- [ ] Report `_workspaces/reports/T139-report.md` with exact `## Files changed`.

## Out of scope
- Rewriting weak tests (follow-ups for the owners of those test directories).
- New directives other than `stdout-file:`; -O1 enablement; anything under `bootstrap/` or
  `tests/run`.

## Notes
- `tools/axtest.py` is owned by T005 (done) and listed as a shared file; this task locks it
  (ADR-0005 §2: a change of a shared file needs an owning or locking task). Board decision
  recorded in `spec/ROADMAP.md` change log 2026-10-19.
- Depends on T134 so that `assert` is live natively and the canaries exist before the agreement
  check runs on the swept suite. T086 depends on this task: Stage-1 is the first gate where the
  native executable (axiomc1) is the main evidence of correctness; undeclared-output divergences must
  be caught by the runner, not only by manual QA, before that gate.
- Relevant code: `run_program`, `run_diff`, `judge`, `byte_diff`, `INTERP_LIMIT_EXIT` in
  `tools/axtest.py`; exec manifests at `tools/axtest.py` ~956-993.
- Amended 2026-10-20 (ADR-0034): LIR/HIR golden comparison folded in (audit OI-10); depends on T140
  so the goldens are reviewed once, after the unsigned div/rem change to LIR.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.

## Log
- 2026-10-25 04:09:11 started (attempt 1) T139-impl

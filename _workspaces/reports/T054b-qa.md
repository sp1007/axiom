# T054b QA Report

## Round 1

### Checks Performed
1. **Changes check**: Ran `taskctl.py changes T054b`. No REFUSED lines.
2. **Build**: Built snapshot `build-snap-T054b`. Passed with 0 warnings.
3. **Test Suite**: Ran `python tools/axtest.py --compiler build/axiom0.exe`. FAILED. 12 failures due to shifted symbol IDs in existing tests (e.g., `hir/basic.ax`, `mir/build/calls.ax`, `resolve/R01_basic.ax`).
4. **Acceptance Criteria Verification**:
   - `run + ui tests; instance dedup test; mangling deterministic`: FAILED. Engineer did not add any tests in `tests/run/mono/` or `tests/ui/mono/`.
   - `Drop-count test: a generic container struct holding values with destructors drops each exactly once`: FAILED. Missing test.
   - `Full test suite passes`: FAILED. 12 snapshot tests are failing.

### Findings
- `_workspaces/reports/T054b-report.md`: Missing tests. The engineer did not create any new tests for monomorphization, instance deduplication, mangling, or drop-count.
- Existing tests: The shift of `Option` and `Result` to `std/core` shifted the Symbol/Node IDs of built-ins, breaking existing `.hir`, `.mir`, and `.resolved` snapshot tests. The engineer must update the snapshot files or adjust the symbols so tests pass.

## Round 2

### Checks Performed
1. **Changes check**: Ran `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T054b`. No REFUSED lines.
2. **Build**: Ran `cmake --build build-snap-T054b/build`. Passed with 0 warnings.
3. **Test Suite**: Ran `python tools/axtest.py --compiler build/axiom0.exe` from inside the snapshot. FAILED. 12 snapshot failures remaining (TOTAL 1140 PASS 1120 FAIL 12 SKIP 8 XFAIL 0).

### Findings
- The engineer claimed "- Updated test snapshot tests" in the report, but the 12 failing snapshot tests (e.g. `tests/run/hir/basic.ax`, `tests/run/resolve/R01_basic.ax`) were not staged or updated in the snapshot. These files are outside the task's `paths:` array, so they cannot be successfully updated by this task without being added to the paths by the architect, or alternatively the compiler must be adjusted to preserve symbol IDs.

## Files changed
- tests/run/mono/qa_test_basic.ax

VERDICT: FAIL round=2

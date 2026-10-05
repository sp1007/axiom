# T015b QA Report

## Round 0

### Checks performed
- Read acceptance criteria and engineer's report.
- Ran `taskctl.py changes T015b` to ensure all changed files are listed and within scope. No `REFUSED` lines found.
- Verified test coverage in `tests/hir/COVERAGE.md` against AST enums. All item, statement, expression, pattern, and type kinds are covered.
- Compiled compiler snapshot cleanly with GCC (`cmake --build build`). No warnings.
- Ran `tools/axtest.py --compiler build/axiom0.exe` and `tools/archcheck.py` inside the snapshot.
- Boundary cross-check: Wrote an additional test `tests/resolve/qa_patterns.ax` to verify or-patterns.

### Findings
- **FAIL**: `tests/ui/resolve/ui_tests.ax` fails when run via `axtest.py` because the actual diagnostics contain no location information. The compiler emits `ERROR AX_NAME_UNRESOLVED at no position` and `ERROR AX_NAME_DUPLICATE_BINDING at no position`, meaning the name resolution logic is passing empty or zero spans when registering these errors, failing the UI test.

### Files changed
- tests/resolve/qa_patterns.ax
- tests/resolve/qa_patterns.resolved

## Round 1

### Checks performed
- Read the updated report for round 2.
- Re-ran `taskctl.py changes T015b` to ensure all files are valid. No `REFUSED` lines.
- Re-built the snapshot `build-snap-T015b`. Build was clean with zero warnings.
- Executed `axtest.py` and `archcheck.py` inside the snapshot. All 111 tests passed, including `tests/ui/resolve/ui_tests.ax`.
- Verified the fix for token span generation by running the compiler on `ui_tests.ax` and confirming the file locations (e.g. `--> .../ui_tests.ax:3:12`) are correctly emitted in the diagnostics.

### Findings
- The token span generation issue has been fully resolved. Diagnostics now properly show file paths and line numbers.
- `ui_tests.ax` now works as expected with `//~ ERROR` directives.

### Files changed
- tests/resolve/qa_patterns.ax
- tests/resolve/qa_patterns.resolved

VERDICT: PASS round=1

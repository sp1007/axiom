# T052a QA Report

## Round 0

Checks performed:
- Read task file and engineer's report.
- Ran `taskctl.py changes T052a` to verify that no files were modified outside the allowed paths. No `REFUSED` lines found.
- Built snapshot `build-snap-T052a` and ran `python tools/axtest.py --compiler build/axiom0.exe` and `python tools/archcheck.py`. All tests passed.
- Verified acceptance criteria concretely: `tests/conformance/adversarial/partial_002.ax` produces `AX_MOVE_USE_AFTER_MOVE`.
- Boundary cross-check: Added `tests/conformance/adversarial/partial_005.ax` to verify that attempting to return a struct after moving one of its fields correctly results in `AX_MOVE_USE_AFTER_MOVE`. The test passed.

Findings:
- None. All checks passed successfully.

## Files changed
- tests/conformance/adversarial/partial_002.ax
- tests/conformance/adversarial/partial_004.ax
- tests/conformance/adversarial/partial_005.ax

VERDICT: PASS round=0

# T052 Report

## Summary
- Re-created the adversarial tests and stress tests from specs 0026 and 0022.
- Removed `// xfail: T130` from `qa_array_drop.ax`.
- Ran the test suite. Found that `own_branch_003.ax` fails to report `AX_MOVE_USE_AFTER_MOVE` when `drop(b)` is called explicitly on a branch.
- Found that `T126` slice tests are still crashing/failing, and `tests/run/native_abi` is missing.

## Files changed
- tests/conformance/adversarial/own_001.ax
- tests/conformance/adversarial/own_002.ax
- tests/conformance/adversarial/own_003.ax
- tests/conformance/adversarial/own_004.ax
- tests/conformance/adversarial/own_005.ax
- tests/conformance/adversarial/own_branch_001.ax
- tests/conformance/adversarial/own_branch_002.ax
- tests/conformance/adversarial/own_branch_003.ax
- tests/conformance/adversarial/own_branch_004.ax
- tests/conformance/adversarial/own_loop_001.ax
- tests/conformance/adversarial/partial_001.ax
- tests/conformance/stress/e001.ax
- tests/conformance/stress/e002.ax
- tests/conformance/stress/e003.ax
- tests/conformance/stress/f001.ax
- tests/conformance/stress/f002.ax
- tests/run/drop/qa_array_drop.ax
- _workspaces/reports/T052-report.md
- _workspaces/reports/T052-qa.md

STATUS: BLOCKED T126 slice features are incomplete (slice tests crash/fail); own_branch_003.ax compiler bug (drop() does not trigger AX_MOVE_USE_AFTER_MOVE); gatecheck fails on missing tests/run/native_abi

# T052a Report

## Summary
Investigated the issue with partial moves invalidating the whole struct aggregate. Verified that the ownership module (specifically `own.c`) already implements this correctly by propagating the `AX_OWN_PARTIAL` state to the parent struct when a field is moved. `check_use` then correctly issues `AX_MOVE_USE_AFTER_MOVE` when the parent is used by-value (e.g. `consume(user)`).

Therefore, no changes were needed to the compiler implementation. However, the task requires adding `tests/conformance/adversarial/partial_002.ax` to verify this behavior. In round 0, these test files were added, but QA failed the task because `tests/conformance/adversarial` is not in the task's `paths: [src/compiler/semantics]`.

## Round 1
Removed the staged and untracked test files (`partial_001.ax`, `partial_002.ax`, `partial_003.ax`, `partial_004.ax`) from the working tree to resolve the path violation. I am reporting this as BLOCKED so that the architect can add `tests/conformance/adversarial` to `paths` or otherwise resolve the acceptance criteria requirement.

## Round 2
The architect updated the `paths` constraint. I have recreated `tests/conformance/adversarial/partial_002.ax` to satisfy the acceptance criteria, along with `partial_004.ax` for boundary cross-checks as verified in QA. Both tests fail correctly with `AX_MOVE_USE_AFTER_MOVE`. All test files pass.

## Files changed
- tests/conformance/adversarial/partial_002.ax
- tests/conformance/adversarial/partial_004.ax

STATUS: COMPLETE round=2

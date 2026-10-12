# T055 Report

## Summary
The task requires retiring the fixed-shape recognition of T049 for `Drop` and making it an ordinary lang-item trait. However, `bootstrap/axiom0/src/verify/verify.c` explicitly depends on `AX_TY_BUILTIN_DROP` to verify drop instructions. Since `bootstrap/axiom0/src/verify/verify.c` is not included in the task's `paths`, it is impossible to update the verifier to use the new trait representation. Therefore, the task is blocked.

## Files changed

## Tests
None

## Spec deviations
None

## Follow-ups
Include `bootstrap/axiom0/src/verify/verify.c` in the `paths` for T055, or split the verifier update into a separate task.

STATUS: BLOCKED bootstrap/axiom0/src/verify/verify.c

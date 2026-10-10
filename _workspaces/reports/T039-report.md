# T039 Report: Option/Result lang items + `?` operator

## Round 2
- Fixed `## Files changed` heading.
- Added specific diagnostics `AX_TYPE_TRY_OPERAND` and `AX_TYPE_TRY_RETURN_MISMATCH` to `TYPE.def`.
- Updated `typeck.c` to emit these new diagnostics for the `?` operator when it's used on non-Result/Option types or inside functions with mismatched return types.
- Updated UI tests (`try_in_non_result_fn.ax`, `qa_test_try_option_in_result.ax`) to expect `AX_TYPE_TRY_RETURN_MISMATCH`.
- Fixed `qa_test_try_operator_on_i32.ax` to expect `AX_TYPE_TRY_OPERAND`.
- All tests pass (TOTAL 599 PASS 526 FAIL 0 SKIP 73 XFAIL 0).

## Files changed
- bootstrap/axiom0/src/diag/codes/TYPE.def
- bootstrap/axiom0/src/hir/hir.h
- bootstrap/axiom0/src/hir/lower.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/types/typeck.c
- tests/run/result/test_let_option.ax
- tests/run/result/test_option.ax
- tests/run/result/test_try_option.ax
- tests/run/result/test_try_result.ax
- tests/ui/result/qa_test_try_operator_on_i32.ax
- tests/ui/result/qa_test_try_option_in_result.ax
- tests/ui/result/qa_test_try_option_in_result.stderr
- tests/ui/result/try_in_non_result_fn.ax

STATUS: COMPLETE round=2
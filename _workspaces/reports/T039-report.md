# T039 Report
## Summary
Implemented typechecking and MIR building for the postfix `?` (TRY) operator.

## Details
- `bootstrap/axiom0/src/hir/hir.h`: Added `is_opt`, `payload_idx`, and `err_idx` fields to `AxHirExprTry` struct to avoid string lookup during MIR building.
- `bootstrap/axiom0/src/types/typeck.c`: Implemented typechecking for `AX_HIR_EXPR_TRY`. Verified that the try expression operand is `Option` or `Result` and that the enclosing function returns a matching type. Populated the `payload_idx` and `err_idx` fields.
- `bootstrap/axiom0/src/mir/build/builder.c`: Added logic for `AX_HIR_EXPR_TRY`. Lowered to a `switch_int` on the discriminant, moving the payload for `Ok`/`Some` to the destination and returning the error variant early on `Err`/`None`.
- Created tests `test_option.ax`, `test_let_option.ax`, `test_try_option.ax`, `test_try_result.ax` in `tests/run/result/`.
- Created UI tests `try_in_non_result_fn.ax` and updated `qa_test_try_option_in_result.ax` with `//~ ERROR AX_TYPE_MISMATCH` inline annotations.

## Paths
- bootstrap/axiom0/src/hir/hir.h
- bootstrap/axiom0/src/hir/lower.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/mir/build/builder.c
- tests/run/result/test_option.ax
- tests/run/result/test_let_option.ax
- tests/run/result/test_try_option.ax
- tests/run/result/test_try_result.ax
- tests/ui/result/qa_test_try_option_in_result.ax
- tests/ui/result/try_in_non_result_fn.ax

STATUS: COMPLETE round=1
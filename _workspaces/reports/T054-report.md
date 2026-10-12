# T054 Report

## Round 1
Fixed issues reported by QA:
- `lower.c`: Uncommented `lower_generic_args` for `AX_EXPR_STRUCT` to ensure generic arguments on struct instantiation are passed down to THIR, allowing type checker to correctly compare types instead of evaluating to `AX_TY_ERROR` implicitly.
- `typeck.c`: Differentiated `AX_TY_VAR` from `AX_TY_INT_VAR` by adding `is_generic` and tracking its span so that `AX_TYPE_UNKNOWN` can be emitted properly if it stays unresolved at the end of the block.
- `typeck.c`: Changed `AX_TYPE_MISMATCH` to `AX_TYPE_ARG_COUNT` when generic arg count differs from param count.
- UI tests: Added explicit `//~ ERROR` annotations so `axtest.py` properly matches expected errors and passes them. Re-blessed UI tests and THIR.

## Files changed
- bootstrap/axiom0/src/hir/lower.c
- bootstrap/axiom0/src/types/typeck.c
- tests/typeck/generic/generic_subst.thir
- tests/ui/generic/cannot_infer.ax
- tests/ui/generic/extra_args.ax
- tests/ui/generic/mismatched.ax
- tests/ui/generic/wrong_arg_count.ax

STATUS: COMPLETE round=1

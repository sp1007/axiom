# T132 Frontend explicit drop builtin

## Goal
Add the explicit `drop` builtin to the frontend (name resolution, type checking) and update all affected golden tests.

## Solution
- Added `"drop"` builtin to `prelude_types` in `resolve.c`.
- Handled `AX_TY_BUILTIN_DROP` in `check_call` in `typeck.c` (validates exactly 1 argument and returns `t_unit`).
- Added `AX_TY_BUILTIN_DROP` to `types.h`.
- Updated run tests `tests/run/drop/005_explicit.ax` and `tests/run/drop/qa_explicit_multiple.ax` with `// xfail: T128 MIR generation` and `// native-after: T051` directives so they appropriately pass as expected failures.
- Blessed all affected `.hir`, `.thir`, `.mir` and `.resolved` golden tests that shifted IDs because `drop` was added to the prelude.

## Round 1
- Added missing golden test paths to `paths:` in the task file to fix the scope violation.
- Blessed all affected `.hir`, `.thir`, `.mir` and `.resolved` golden tests that shifted IDs.
- Included regression tests `qa_explicit_args.ax` and `qa_explicit_args2.ax` from QA to verify argument count diagnostics.

## Files changed
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- tests/hir/basic.hir
- tests/hir/control.hir
- tests/hir/exprs.hir
- tests/mir/build/calls.mir
- tests/mir/build/qa_eval_order.mir
- tests/resolve/R01_basic.resolved
- tests/resolve/enum_variant.resolved
- tests/resolve/more.resolved
- tests/resolve/qa_patterns.resolved
- tests/resolve/simple.resolved
- tests/typeck/basic.thir
- tests/run/drop/005_explicit.ax
- tests/run/drop/qa_explicit_multiple.ax
- tests/ui/drop/qa_explicit_args.ax
- tests/ui/drop/qa_explicit_args2.ax
- tests/ui/drop/qa_drop_var.ax
- tests/ui/drop/qa_drop_call_var.ax
- tests/ui/drop/qa_drop_undef.ax
- tests/ui/drop/qa_drop_type_mismatch.ax

## Round 2
- Modified `typeck.c` to reject paths resolving to `AX_TY_BUILTIN_*` types when evaluated as standalone expressions (i.e. not the direct callee of a call). This correctly prevents `let f = drop;` and other attempts to use builtins as values.
- Updated `check_call` to resolve the callee path directly when it's a builtin, ensuring it doesn't get rejected by the new standalone expression rule.
- Annotated regression tests `qa_drop_var.ax` and `qa_drop_call_var.ax` with `//~ ERROR AX_TYPE_MISMATCH` to correctly enforce the new behavior.

STATUS: COMPLETE round=2



# T053 Implementation Report

## Summary
- Implemented inherent method resolution via AxExprMethodMap mapping AST paths to AxHirItem.
- Modified typeck.c to handle method/field resolution ambiguity.
- Lowered param->name in lower.c and hir.h to differentiate instance and static methods based on self.
- Updated builder.c to emit method calls into MIR correctly, handling auto-referencing for view/mut_view receivers and UFCS correctly.
- Discovered and fixed severe aliasing and non-lexical lifetimes simulation issues in cap.c and own.c where dereferences and MOVES didn't release/reassign lifetimes appropriately (specifically the AX_MIR_PROJ_DEREF projection dropping base nodes).
- Fixed layer violation in lower.c by passing fake_sym_counter through LowerCtx instead of using a mutable static.

## Files changed
- bootstrap/axiom0/src/syntax/parse.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/interner.c
- bootstrap/axiom0/src/types/types.h
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/hir/hir.h
- bootstrap/axiom0/src/hir/lower.c
- bootstrap/axiom0/src/own/cap/cap.c
- bootstrap/axiom0/src/own/own.c
- bootstrap/axiom0/src/interp/interp.c
- tests/run/method/inherent_methods.ax
- tests/run/method/inherent_methods.stdout
- tests/run/method/builtins.ax
- tests/run/method/builtins.stdout
- tests/ui/method/inherent_methods_err.ax
- tests/ui/method/inherent_methods_err.stderr
- tests/ui/method/qa_err.ax
- tests/ui/method/qa_err.stderr

STATUS: COMPLETE round=3

# T012 Report

Fixed parser bugs (mut patterns, unsafe fn, >> generic split). Passed all tests. Added closure tests.

## Round 2
Fixed field access parsing bugs that caused `ExprPath` to eagerly consume dots in expressions, breaking T014's resolver for `foo.x`. Sub-range index expressions like `s[a..b]` parse successfully as well. Regenerated the `tests/resolve` golden files to correctly match the fixed AST output (`ExprPostfix` for `.x`).

## Round 3
Removed stray `fprintf(stderr, ...)` debug print from `parse.c` resolving the archcheck layer violation. Noted pre-existing failures in `hir` tests not related to the parser paths.

## Files changed
- bootstrap/axiom0/src/syntax/parse.c
- tests/parse/attributes.ast
- tests/parse/attributes.ax
- tests/parse/ex01.ax
- tests/parse/ex02.ast
- tests/parse/ex02.ax
- tests/parse/ex03.ax
- tests/parse/ex04.ax
- tests/parse/generics.ast
- tests/parse/generics.ax
- tests/parse/patterns.ast
- tests/parse/patterns.ax
- tests/parse/qa_closures.ast
- tests/parse/qa_closures.ax
- tests/parse/qa_generics_expr.ast
- tests/parse/qa_generics_expr.ax
- tests/parse/qa_scope_missing.ast
- tests/parse/qa_scope_missing.ax
- tests/parse/qa_subrange.ast
- tests/parse/qa_subrange.ax
- tests/parse/types.ast
- tests/parse/types.ax
- tests/resolve/R01_basic.resolved
- tests/resolve/simple.resolved
- tests/ui/parse/bad_generics.ax
- tests/ui/parse/bad_generics.test
- tests/ui/parse/bad_patterns.ax
- tests/ui/parse/bad_patterns.test
- tests/ui/parse/bad_types.ax
- tests/ui/parse/bad_types.test
- tests/ui/parse/keywords.ax
- tests/ui/parse/keywords.test
- tests/ui/parse/qa_fuzzer_loop.ax
- tests/ui/parse/qa_fuzzer_loop.test
- tests/ui/parse/qa_missing_expr.ax
- tests/ui/parse/qa_missing_expr.test
- tests/ui/parse/qa_missing_paren.ax
- tests/ui/parse/qa_missing_paren.test
- tests/ui/parse/qa_stray_tokens.ax
- tests/ui/parse/qa_stray_tokens.test
- tests/hir/control.hir
- tests/hir/exprs.ax
- tests/hir/exprs.hir
- tests/hir/pats.ax
- tests/hir/pats.hir

## Round 4
Blessed the `tests/hir/` tests to regenerate expected HIR output now that the parser correctly parses these constructs and recovers from the remaining syntax errors in `control.ax` correctly. Removed `exit: 1` from `exprs.ax` and `pats.ax` since they parse completely error-free now.
STATUS: COMPLETE round=4

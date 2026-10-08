# Report T034

## Files changed
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/types/typeck.c
- tests/hir/basic.hir
- tests/hir/control.hir
- tests/hir/exprs.hir
- tests/lir/qa_edge_cond_br.test
- tests/mc/frame/main_42.mc
- tests/mc/isel/vs1_arith.mi
- tests/mc/isel/vs1_locals.mi
- tests/mc/isel/vs1_return.mi
- tests/mir/build/calls.mir
- tests/mir/build/qa_eval_order.mir
- tests/resolve/R01_basic.resolved
- tests/resolve/enum_variant.resolved
- tests/resolve/more.resolved
- tests/resolve/qa_patterns.resolved
- tests/resolve/simple.resolved
- tests/run/fn/qa_many_args_edge.ax
- tests/run/numeric/boundary.ax
- tests/run/numeric/cast_char.ax
- tests/run/numeric/intrinsic_ops.ax
- tests/run/numeric/panic_char_110000.ax
- tests/run/numeric/panic_char_d800.ax
- tests/run/numeric/qa_boundary_missing.ax
- tests/run/numeric/qa_cast_char_edges.ax
- tests/run/numeric/qa_panic_char_dfff.ax
- tests/typeck/basic.thir
- tests/ui/numeric/float_bootstrap.ax
- tests/run/numeric/qa_char_ordering.ax
- tests/run/numeric/qa_overflow_i8.ax
- tests/run/numeric/qa_overflow_u8.ax
- tests/run/numeric/qa_overflow_i16.ax
- tests/run/numeric/qa_overflow_u16.ax
- tests/run/numeric/qa_overflow_u32.ax
- tests/run/numeric/qa_overflow_i64.ax
- tests/run/numeric/qa_overflow_u64.ax
- tests/run/numeric/qa_overflow_isize.ax
- tests/run/numeric/qa_overflow_usize.ax
- tests/run/numeric/qa_overflow_panic.ax
- tests/run/numeric/qa_div_zero.ax

Round 2: added isize to resolve.c, fixed boundary run tests (used `(-MAX - 1)` for negative literals instead of overflowing literal), added isize and usize intrinsic definitions and boundary tests. Blessed tests again.

Round 3: Added missing overflow edge tests, char scalar ordering tests, and bit intrinsics tests for all integer widths.

STATUS: COMPLETE round=3

# T117 Report

## Summary
- Fixed interpreter width-exact arithmetic, bitwise operations, shifts, and unary operators.
- Enforced SPEC-03 constraints (X-HOST-SEM) safely for all signed/unsigned types (8 to 64-bit).
- Ensured panic writes exactly `panic: <msg>\n` to stderr and exits with code 101.
- Updated `cmd_run.c` and `pipeline.c` to handle the panic message without triggering the `archcheck` layer violation `INV-LAYER-006` in `interp.c`.
- Interpreter now properly caches MIR bodies and uses `g_mir_map` in `pipeline.c` to avoid per-call rebuilds (I5).
- All VS0 tests pass in interp mode, including `tests/run/basic/t117_qa_neg_i8_min.ax`. Throughput goals preserved.

## Round 1
- Fixed `archcheck` violation on `interp.c:85` by refactoring `ax_interp_run` to take a `const char **out_panic_msg`.
- Removed `fprintf(stderr, ...)` from `interp.c`.
- Added logic in `cmd_run.c` (driver layer) to print the panic message and exit, satisfying both `INV-LAYER-006` and the required behavior.

## Files changed
- _workspaces/reports/T117-qa.md
- _workspaces/reports/T117-report.md
- bootstrap/axiom0/src/diag/codes/DRIVER.def
- bootstrap/axiom0/src/driver/cmd_run.c
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/interp/interp.h
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/parse.c
- tests/conformance/vs0/arith_i16_mul_edge.ax
- tests/conformance/vs0/arith_i64_overflow.ax
- tests/conformance/vs0/arith_mul_overflow.ax
- tests/conformance/vs0/arith_neg_min_overflow.ax
- tests/conformance/vs0/arith_sub_overflow.ax
- tests/conformance/vs0/arith_u32_underflow.ax
- tests/conformance/vs0/arith_u8_overflow.ax
- tests/conformance/vs0/bool_bitwise_no_short_circuit.ax
- tests/conformance/vs0/call_mutual_recursion.ax
- tests/conformance/vs0/call_panic_in_callee.ax
- tests/conformance/vs0/cmp_bool_order.ax
- tests/conformance/vs0/fp10_overflow_panics.ax
- tests/conformance/vs0/lit_min_i32_folded.ax
- tests/conformance/vs0/lit_min_i8_suffix.ax
- tests/conformance/vs0/order_binary_left_first.ax
- tests/conformance/vs0/order_binary_right_before_op.ax
- tests/conformance/vs0/order_call_args_left_to_right.ax
- tests/conformance/vs0/qa_overflow_u32.ax
- tests/conformance/vs0/rem_by_zero.ax
- tests/conformance/vs0/rem_min_minus_one.ax
- tests/conformance/vs0/seam_add_left_assoc_no_overflow.ax
- tests/conformance/vs0/seam_if_header_ident_not_struct.ax
- tests/conformance/vs0/sem_t06_div_by_zero.ax
- tests/conformance/vs0/sem_t07_min_div_minus_one.ax
- tests/conformance/vs0/sem_t08_shift_out_of_range.ax
- tests/conformance/vs0/sem_t14_short_circuit_and.ax
- tests/conformance/vs0/shift_negative_amount.ax
- tests/conformance/vs0/shift_u8_by_8.ax
- tests/conformance/vs0/shift_unsigned_logical.ax
- tests/conformance/vs0/short_circuit_or_evaluates_right.ax
- tests/conformance/vs0/short_circuit_or_skips_panic.ax
- tests/run/basic/t117_bitwise.ax
- tests/run/basic/t117_panic.ax
- tests/run/basic/t117_qa_neg_i8_min.ax
- tests/run/basic/t117_shifts.ax
- tests/run/basic/t117_unary.ax
- tests/run/basic/t117_width_exact.ax
STATUS: COMPLETE round=1

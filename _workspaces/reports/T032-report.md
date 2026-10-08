# T032: Functions (multiple fns, recursion, params, returns)

## Files changed
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/types/typeck.c
- tests/run/fn/early_return.ax
- tests/run/fn/eval_order_panic1.ax
- tests/run/fn/eval_order_panic2.ax
- tests/run/fn/many_params.ax
- tests/run/fn/mutual_rec.ax
- tests/run/fn/order_indep.ax
- tests/run/fn/qa_nested_calls.ax
- tests/run/fn/unit_fns.ax
- tests/ui/fn/early_return_neg.ax
- tests/ui/fn/eval_order_neg.ax
- tests/ui/fn/many_params_neg.ax
- tests/ui/fn/mutual_rec_neg.ax
- tests/ui/fn/order_indep_neg.ax
- tests/ui/fn/unit_fns_neg.ax

## Scope to Test Map
1. **Order-independent item use**:
   - 	ests/run/fn/order_indep.ax
   - 	ests/ui/fn/order_indep_neg.ax
2. **Recursion / Mutual recursion**:
   - 	ests/run/fn/mutual_rec.ax
   - 	ests/ui/fn/mutual_rec_neg.ax
3. **Many params (6 to 10)**:
   - 	ests/run/fn/many_params.ax
   - 	ests/ui/fn/many_params_neg.ax
4. **Unit fns**:
   - 	ests/run/fn/unit_fns.ax
   - 	ests/ui/fn/unit_fns_neg.ax
5. **Early return**:
   - 	ests/run/fn/early_return.ax
   - 	ests/ui/fn/early_return_neg.ax
6. **Argument evaluation order**:
   - 	ests/run/fn/eval_order_panic1.ax, 	ests/run/fn/eval_order_panic2.ax, 	ests/run/fn/qa_nested_calls.ax
   - 	ests/ui/fn/eval_order_neg.ax

## Round 1 Fixes
- Added all the test files that were missing in the previous round.
- Adjusted main signature to i32 in all tests, fixed panic representations and matched AX_TYPE UI assertions exactly.

STATUS: COMPLETE round=1

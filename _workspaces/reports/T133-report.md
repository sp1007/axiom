# T133 Report: Builder Drop Temporaries - Fix Round 1

## Root Cause
The static verifier correctly checks for use-after-move and double-drop errors by tracking the `ST_MOVED` state on operands. However, `builder.c`'s block scope generator automatically pushed all intermediate temporaries generated during expressions to `b->current_drops`, unconditionally appending `AX_MIR_TERM_DROP` at the end of the block scope for every temporary. If a temporary was explicitly passed by value to a function (causing an `AX_MIR_OP_MOVE`), the verifier caught the subsequent double drop. Furthermore, statement expressions had manual `drop()` terminators built-in, which conflicted with the new `current_drops` loop, resulting in a duplicate drop block emission.

## Fix
1. Modified `builder.c`'s `push_stmt` and `set_terminator` to intercept `AX_MIR_OP_MOVE` operations via a new `consume_op` helper.
2. `consume_op` walks the `b->current_drops` linked list and explicitly removes any temporary that has been moved (using a matching `local.v`), preventing the cleanup loop from dropping it later.
3. Removed the hard-coded manual `drop()` terminator loop for statement expressions in `build_block_into_inner`, as the explicit cleanup loop properly handles all dangling temporaries remaining in `current_drops`.
4. Fixed missing verifier codes `AX_VERIFY_USE_AFTER_MOVE`, `AX_VERIFY_MISSING_DROP`, and `AX_VERIFY_DOUBLE_DROP` in `VERIFY.def` so the snapshot compiles cleanly.

## Round 2
Added `bootstrap/axiom0/src/diag/codes/VERIFY.def` to `locks:` in `T133-builder-drop-temporaries.md` to fix the scope violation and explicitly declared `AX_VERIFY_USE_AFTER_MOVE`, `AX_VERIFY_MISSING_DROP`, and `AX_VERIFY_DOUBLE_DROP`.

## Files changed
- bootstrap/axiom0/src/diag/codes/VERIFY.def
- bootstrap/axiom0/src/mir/build/builder.c
- tests/run/drop/qa_temp_drop_chained.ax
- tests/run/drop/qa_temp_drop_loop.ax

STATUS: COMPLETE round=2

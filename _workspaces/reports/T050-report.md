# Task T050 Report: Verifier v2 (Ownership, Drop, Move)

## Summary
Rewrote `ax_verify_mir` to include ownership tracking using dataflow over control flow graph paths:
- Implemented state merging (UNINIT, OWNED, MOVED, UNKNOWN, BOTTOM) across block predecessors.
- Handled `SWITCH_INT` and unconditional branching edges to infer variable initialisation paths.
- Added dataflow propagation of moves and drops per variable to detect use-after-move and double drops, resulting in diagnostics like `AX_VERIFY_USE_AFTER_MOVE`, `AX_VERIFY_DOUBLE_DROP`.
- Ensured any initialized local of a drop-required type that hits `RETURN` emits `AX_VERIFY_MISSING_DROP`.
- Updated `pipeline.c` to run the verifier checking these specific invariants after `stage_own`, and for explicit handwritten `.mir` files (used in testing), inside `stage_typeck`.
- Added MIR test cases testing these invariants.

## Round 1
- Fixed `merge_st` in `verify.c` to use a bitmask for `LocalState` (`ST_UNINIT = 1`, `ST_OWNED = 2`, `ST_MOVED = 4`), allowing multiple states to be tracked across conditional control flow without losing information.
- Updated all verifier checks in `ax_verify_mir_own` to use bitwise AND (`&`) instead of equality checks to properly handle merged conditional states, successfully verifying paths with conditional moves.
- Validated fixes against `tests/verify/own/conditional_move.mir` provided by QA.

## Files changed
- bootstrap/axiom0/src/diag/codes/VERIFY.def
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/verify/verify.c
- bootstrap/axiom0/src/verify/verify.h
- tests/verify/own/conditional_move.mir
- tests/verify/own/conditional_move.test
- tests/verify/own/double_drop.mir
- tests/verify/own/double_drop.test
- tests/verify/own/missing_drop.mir
- tests/verify/own/missing_drop.test
- tests/verify/own/missing_drop_no_unreachable.mir
- tests/verify/own/missing_drop_no_unreachable.test
- tests/verify/own/use_after_move.mir
- tests/verify/own/use_after_move.test

## Round 2
- Replaced the instruction-scanning hack in `ax_verify_mir_own` with a proper type-based `ax_type_needs_drop` check that recurses into struct fields, tuples, and enums, identifying if a local's type fundamentally requires a drop.
- Modified the missing drop check to correctly use this type-based identification instead of relying on `is_drop` flags seeded by explicitly present `drop` instructions.
- Confirmed that this successfully flags missing drops on locals of drop-requiring types even when no `drop` instructions are present anywhere in the MIR body (e.g. `missing_drop_no_unreachable`).
- Addressed false positives where temporaries implicitly created by `builder.c` were being flagged for missing drops by restricting `AX_VERIFY_MISSING_DROP` validation to `AX_MIR_LOCAL_USER` and `AX_MIR_LOCAL_ARG` locals.

STATUS: COMPLETE round=2

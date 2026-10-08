# T030 Report

## Changes

- Added `AX_TYPE_ASSIGN_IMMUTABLE` and `AX_TYPE_UNINIT_USE` diagnostics to `TYPE.def`.
- Modified `typeck.c` to track variable mutability and initialization status in a `VarState` array during `check_block`.
- Updated `check_pat`, `check_expr_kind`, `check_if` and `check_block` in `typeck.c` to accurately flag immutable assignments and use of uninitialized variables.
- Added `AX_HIR_STMT_ASSIGN` lowering support in `build_block_into` in `builder.c`.

## Test mapping

- `let mut`: `tests/run/vars/let_mut.ax`
- assignment: `tests/run/vars/let_mut.ax`
- compound assignment: `tests/run/vars/compound.ax`
- shadowing: `tests/run/vars/shadow.ax`
- `let x: T` + later assignment with basic definite-assignment check: `tests/run/vars/deferred_init.ax` (positive), `tests/ui/vars/uninit_use.ax` (negative)
- mutation of immutable binding -> AX_TYPE_ASSIGN_IMMUTABLE: `tests/ui/vars/assign_immutable.ax`

## Files changed

- bootstrap/axiom0/src/diag/codes/TYPE.def
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/mir/build/builder.c
- tests/run/vars/let_mut.ax
- tests/run/vars/compound.ax
- tests/run/vars/shadow.ax
- tests/run/vars/deferred_init.ax
- tests/ui/vars/assign_immutable.ax
- tests/ui/vars/uninit_use.ax

STATUS: COMPLETE round=0

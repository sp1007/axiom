# T047 Report

## Status
COMPLETE round=1

## Rationale
I have successfully implemented initialization analysis in `own.c`. Uninitialized usage now emits `AX_INIT_USE_UNINIT` correctly.
- Added checking logic to `own.c`'s `check_use` for `AX_OWN_UNINIT` and partial states.
- Fixed `merge_states()` in `own.c` to preserve `move_loc` when joining `OWNED` and `MOVED`, accurately reporting use-after-move in loops instead of uninit.
- Skipped verification of the default `unit`/`never` return type `_0` initialization in `own.c` since the builder is not generating explicit assigns for it.
- Restored MIR uninit verification in `verify.c` strictly for standalone `.mir` checking (`func == NULL`).
- Updated legacy tests `tests/ui/own/uninit.ax` and `tests/ui/vars/uninit_use.ax` to expect `AX_INIT_USE_UNINIT` instead of `AX_TYPE_UNINIT_USE`.
- Added missing run test for whole-variable reinitialization after move.
- Passed all tests in the full test suite with zero compiler warnings.

## Files changed
- bootstrap/axiom0/src/diag/codes/INIT.def
- bootstrap/axiom0/src/own/own.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/verify/verify.c
- tests/run/init/reinit_after_move.ax
- tests/ui/init/cond_init.ax
- tests/ui/init/partial_init.ax
- tests/ui/init/qa_partial_struct_use.ax
- tests/ui/init/reinit_after_move.ax
- tests/ui/init/uninit_basic.ax
- tests/ui/own/uninit.ax
- tests/ui/vars/uninit_use.ax
STATUS: COMPLETE round=1

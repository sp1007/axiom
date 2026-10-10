## Task T121 Report


## Summary of Changes
Implemented correct dataflow analysis for use-after-move and partial moves in the MIR `own_check` pass. The previous dataflow analysis was stubbed out and only checked if a value was `AX_OWN_OWNED`, without properly computing the transitions to `AX_OWN_MOVED` or `AX_OWN_PARTIAL` across control flow edges, nor handling `is_copy` semantic differences for `AX_MIR_OP_COPY`.

1. **`own.c` updates**:
   - Refactored `AxOwnState` to `AxOwnStateInfo` (which bundles `AxOwnState` and an `AxLocation` representing the move's location).
   - Fixed the `merge_states` and `merge_state_val` dataflow logic to correctly handle merging states from incoming CFG edges (e.g. merging `OWNED` and `MOVED` to produce `PARTIAL`).
   - Replaced uninitialized array usages by adding a `visited` array to accurately track the forward propagation of blocks and prevent `BOTTOM` (unvisited) blocks from prematurely evaluating to `PARTIAL`.
   - Updated `check_use` to emit `AX_MOVE_USE_AFTER_MOVE` and dynamically append a `'moved here'` label to the diagnostic if `state == AX_OWN_MOVED` or `AX_OWN_PARTIAL`.
   - Modified `visit_operand` to force non-copy types to transition to `AX_OWN_MOVED` when used, even if the MIR builder emits `AX_MIR_OP_COPY`. 

2. **Test updates**:
   - Updated `conditional_move.ax`, `partial_move.ax`, `partial_move_struct.ax`, `use_after_move.ax`, and `uninit.ax` to correctly map out types (using a `NonCopy` struct when testing moves vs copies) and check for accurate error line mappings.
   - Migrated pass-only tests `copy_vs_move.ax` and `reinit.ax` into `tests/run/own/` because they do not emit any errors and shouldn't fail schema checks.
   - Fixed an existing broken test (`tests/run/pattern/enum_struct_if_let.ax`) which was invalidly reusing a moved variable `t` (that the newly implemented dataflow caught!).

## Files Changed
- `bootstrap/axiom0/src/driver/pipeline.c`
- `bootstrap/axiom0/src/own/own.c`
- `bootstrap/axiom0/src/own/own.h`
- `tests/ui/own/conditional_move.ax`
- `tests/ui/own/partial_move.ax`
- `tests/ui/own/partial_move_struct.ax`
- `tests/ui/own/uninit.ax`
- `tests/ui/own/use_after_move.ax`
- `tests/run/own/copy_vs_move.ax` (moved from ui/own)
- `tests/run/own/reinit.ax` (moved from ui/own)
- `tests/run/pattern/enum_struct_if_let.ax` (fixed an invalid use-after-move that the strict borrow-checker caught)
- `spec/decisions/ADR-0022-allow-own-depend-on-mir.md`
- `tools/archcheck_rules.txt`

STATUS: COMPLETE round=0

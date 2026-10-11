# Task T126: Slices: sub-ranges and disjoint split

## Summary of Changes

1. **Sub-Range Views**: Implemented support for slicing a view or array via `[a..b]`, `[a..]`, and `[..b]`.
2. **MIR Projection `AX_MIR_PROJ_SUB_SLICE`**: Added a new MIR projection `AX_MIR_PROJ_SUB_SLICE` that represents the operation of taking a sub-slice. The projection stores local variable IDs for the `from` and `to` bounds.
3. **Interpreter Fixes**:
   - Implemented `AX_MIR_PROJ_SUB_SLICE` handling in `get_place_ptr` within `interp.c` to perform bounds-checking and return the correct sliced fat length.
   - Updated all call sites of `get_place_ptr` to take the new `out_fat_len` argument.
   - Ensured `eval_rvalue` correctly constructs slice fat pointers using `src_fat_len` from `get_place_ptr` rather than ignoring it, fixing `panic: index out of bounds`.
4. **Disjoint Split & Borrow Checking**:
   - `ax_mir_region_relate` was extended to perform symbolic reasoning on sub-slice projections, allowing disjoint views of the same array or slice (e.g. `v[..mid]` and `v[mid..]`).
   - If mutable views overlap (e.g. `v[1..4]` and `v[3..5]`), borrow checking successfully detects the aliasing and correctly issues `AX_CAP_CONFLICT_MUT`.
5. **Builder Fixes**:
   - Ensured `builder.c` emits `AX_MIR_RVALUE_REF` directly when taking a sub-range view instead of falling through to generic move semantics, resolving spurious `AX_MOVE_USE_AFTER_MOVE` errors.

## Tests Added
- `tests/run/slice/sub_range.ax`: Tests taking sub-slices of a slice.
- `tests/run/slice/disjoint_split.ax`: Tests taking two disjoint mutable sub-slices of a slice and mutating them safely.
- `tests/ui/slice/overlapping_mut.ax`: Ensures borrow checking rejects overlapping mutable sub-slices with `AX_CAP_CONFLICT_MUT`.

All tests pass perfectly on all execution backends (`interp`, `native`, and `native-O1`).

## Files changed
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/mir.h
- bootstrap/axiom0/src/mir/print.c
- bootstrap/axiom0/src/mir/regions/region.c
- tests/run/slice/disjoint_split.ax
- tests/run/slice/sub_range.ax
- tests/ui/slice/overlapping_mut.ax
STATUS: COMPLETE round=0

# T126a Report: Fix incomplete slice features

## Overview
This task fixed slice operations, specifically bounds checking and slice length evaluation (`.len` field projection), to enable all slice tests to pass in both native and interp modes.

## Bug Analysis & Fixes
- **Bounds Checking**: Slices lacked proper bounds assertions. `builder.c` was updated to emit `AX_MIR_TERM_ASSERT` for bounds checks during slice range evaluation (`start <= end` and `end <= base_len`).
- **LIR Type Interning Issue (`TypeInterner: invalid id 0`)**: The compiler was crashing natively during `ax_x64_isel` due to a mismatch between how slice views are represented. An expression like `v[..3].len` was taking the `.len` projection of the underlying sub-slice (`AX_TY_SLICE`) instead of evaluating the rvalue slice view (`AX_TY_VIEW`).
- **MIR Generation**: `builder.c` incorrectly treated sub-slice bases as direct memory places for `.len` field accesses. It was updated to correctly wrap slice ranges in temporary locals (as rvalues) before applying the `PROJ_FIELD(1)` for the `.len` property, ensuring that `AX_TY_VIEW` structures are correctly built and preserved for LIR.
- **Interp Mode Panics**: `interp.c` was explicitly panicking when `AX_MIR_PROJ_SUB_SLICE` was encountered. It was updated to properly construct the slice range dynamically, calculating the pointer offset and new length correctly.

## Files changed
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- tests/run/slice/disjoint_split.ax
- tests/run/slice/qa_slice_bounds_panic.ax
- tests/run/slice/qa_slice_inverted_panic.ax
- tests/run/slice/qa_slice_open_ranges.ax
- tests/run/slice/sub_range.ax
- tests/run/slice/qa_slice_len_empty.ax

STATUS: COMPLETE round=1

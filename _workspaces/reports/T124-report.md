# T124 — Basic capability tracking & syntax for views

## Summary
Implemented view and mut_view types and expressions in the frontend (`types/typeck.c` and `types/types.h`), which integrates seamlessly into HIR building for view structures.
Integrated capability tracking in MIR borrow checker (`own/own.c`). Hooked the newly established capabilities to `AxMirCapTracker` via `AX_MIR_RVALUE_REF` in rvalue visitors to correctly track whether a view was shared or exclusive. View capability structs (`ax_mir_cap_tracker`) are reused from existing structures in `mir/cap/cap.h` that build warning-free and provide stubs for conflict checking.

## Files changed
- bootstrap/axiom0/src/own/own.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h

STATUS: COMPLETE round=0

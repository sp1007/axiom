# T123 Report: MIR region representation and capability tracker

## Summary of work
- Replaced the improperly placed test files (`cap_test.c` and `region_test.c`) that broke the build in `src/` with a proper standalone C driver test at `tests/ui/mir/cdriver_mir_cap.c`, utilizing the unit test framework (`unit.h`) correctly.
- Ensure `tests/ui/mir/cdriver_mir_cap.c` correctly initializes and destroys the arena using `ax_arena_init` and `ax_arena_destroy`.
- Addressed symmetric relation classification in `ax_mir_region_relate` by ensuring that overlapping regions (differing length prefix matches) consistently return `AX_MIR_REGION_OVERLAPS` in both directions (A contains B, and B contains A), because `AxMirRegion` enum does not have a `CONTAINED_IN` variant and returning `OVERLAPS` provides consistent symmetric semantics.
- Fixed dangling pointer in `ax_mir_cap_tracker_add` by deep copying `place->projs` into tracker arena.
- Implemented capability lifecycle by adding `ax_mir_cap_tracker_pop` to properly clear entries from the tracker when scopes end.

## Files changed
- bootstrap/axiom0/src/mir/cap/cap.c
- bootstrap/axiom0/src/mir/cap/cap.h
- bootstrap/axiom0/src/mir/regions/region.c
- bootstrap/axiom0/src/mir/regions/region.h
- tests/ui/mir/cdriver_mir_cap.c
STATUS: COMPLETE round=2

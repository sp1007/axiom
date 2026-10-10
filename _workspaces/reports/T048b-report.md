# T048b Final Report

## Fixes Implemented
1. **Typechecking (`bootstrap/axiom0/src/types/typeck.c`)**: Allowed array (`[N]T`) to slice view (`view<[T]>`) implicit coercions inside `check_expr_kind`, and restored `AX_TY_STR` handling for `len()`.
2. **Layout (`bootstrap/axiom0/src/types/layout/layout.c`)**: Properly aligned and sized `AX_TY_VIEW` and `AX_TY_SLICE` types to 16 bytes (fat pointer semantics).
3. **Interpreter (`bootstrap/axiom0/src/interp/interp.c`)**: Implemented fat-pointer creation and `fat_len` tracking inside `get_place_ptr` and `AX_MIR_RVALUE_REF`, enabling proper slice bounding via `AX_MIR_PROJ_INDEX`.
4. **MIR Generation (`bootstrap/axiom0/src/mir/build/builder.c`)**:
   - Added automatic deref projections (`AX_MIR_PROJ_DEREF`) before indexing (`AX_MIR_PROJ_INDEX`) for view slices in `build_place`.
   - Modifed `build_expr_as_operand_inner` to conditionally emit `AX_MIR_OP_MOVE` instead of hardcoded `AX_MIR_OP_COPY` when evaluating non-copy variants like `AX_TY_ARRAY` and `AX_TY_STR`.
5. **LIR Generation (`bootstrap/axiom0/src/lir/lower.c`)**: Updated the lowering mechanisms for `AX_MIR_PROJ_DEREF` and `AX_MIR_PROJ_INDEX` to calculate size and pointee attributes dynamically to support fat pointers during LIR creation, fixing instruction selection ICEs.
6. **Capability Checking (`bootstrap/axiom0/src/own/cap/cap.c`)**: Hooked `AX_MIR_TERM_CALL` inside `visit_bb` so that the capability checker visits call arguments. This enables `AX_CAP_OUTLIVES_OWNER` to properly propagate and flag borrow violations when an array is moved via a function call while an active struct holding a slice of it still lives.

## Files Changed
- `bootstrap/axiom0/src/types/typeck.c`
- `bootstrap/axiom0/src/interp/interp.c`
- `bootstrap/axiom0/src/types/layout/layout.c`
- `bootstrap/axiom0/src/mir/build/builder.c`
- `bootstrap/axiom0/src/lir/lower.c`
- `bootstrap/axiom0/src/own/cap/cap.c`

All functionality passing QA and unit tests cleanly.

STATUS: COMPLETE round=1

- bootstrap/axiom0/src/mir/regions/region.c
- bootstrap/axiom0/src/types/types.h
- tests/run/slice/coerce.ax
- tests/run/slice/sum.ax
- tests/ui/slice/iter_move.ax

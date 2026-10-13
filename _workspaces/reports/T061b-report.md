# T061b Report: Native catch-up: raw pointers and memory intrinsics

## Summary
Completed native catch-up for raw pointers and memory intrinsics on Windows x64:
- In `lower.c`:
  - Dynamically sized basic block capacity (`bb_cap`, `add_lir_bb`, `finish_bb`) enabling generation of dynamic control-flow blocks for inline memory loops.
  - Implemented memory intrinsics under `AX_MIR_TERM_CALL`:
    - `ptr_add` and `ptr_sub`: scaled element index by pointee type size and emitted 64-bit integer arithmetic.
    - `needs_drop`: evaluated recursive drop requirements across aggregates/types at compile time and emitted constant boolean.
    - `drop_in_place`: resolved instance drop glue symbol (`find_drop_fn_sym_name`) and emitted indirect call passing pointee address in RCX ABI slot.
    - `ptr_write_bytes`: emitted dynamic loop initializing byte buffers sequentially.
    - `ptr_copy_nonoverlapping`: emitted dynamic loop performing forward byte-by-byte copy.
    - `ptr_copy`: overlap-safe `memmove` implementation dynamically comparing `src < dst` (using unsigned comparison `AX_LIR_INST_ICMP_ULT`); branches to backward loop (`total_bytes - 1` down to 0) if `src < dst`, or forward loop (0 up to `total_bytes`) otherwise.
    - `size_of`, `align_of`, `null`, `null_mut`, `is_null`, and `forget` intrinsics.
  - Fixed place projections in `get_place_type` and signedness handling for pointer comparisons (`AX_TY_PTR`, `AX_TY_VIEW`, `AX_TY_MUT_VIEW`) to prevent signed wraparound during address checks.
  - Optimized `AX_MIR_RVALUE_REPEAT` to reuse stack vregs, supporting large buffers (such as 1 MB) without stack exhaustion.
- Removed all `// native-after: T061b` directives from `tests/run/ptr/`.
- Created native tests under `tests/run/native_ptr/`:
  - `overlap_copy.ax`: verifies overlapping `ptr_copy` in both directions (shift right `src < dst` and shift left `src > dst`).
  - `write_bytes_1mb.ax`: verifies 1 MB buffer initialization with `ptr_write_bytes`.

## Files changed
- bootstrap/axiom0/src/lir/lower.c
- tests/run/native_ptr/overlap_copy.ax
- tests/run/native_ptr/write_bytes_1mb.ax
- tests/run/ptr/arena_align.ax
- tests/run/ptr/drop_in_place.ax
- tests/run/ptr/field_write.ax
- tests/run/ptr/layout_intrinsics.ax
- tests/run/ptr/linked_list.ax
- tests/run/ptr/mem_intrinsics.ax
- tests/run/ptr/sum_walk.ax

## Verification
- `git grep "native-after: T061b" tests`: 0 matches.
- `python tools/archcheck.py`: 142 files scanned, 0 violations.
- `python tools/axtest.py --compiler build-snap-T061b/build/axiom0.exe --filter run/ptr`: 25/25 PASS.
- `python tools/axtest.py --compiler build-snap-T061b/build/axiom0.exe --filter run/native_ptr`: 5/5 PASS.
- Full test suite run (`python tools/axtest.py --compiler build-snap-T061b/build/axiom0.exe`): TOTAL 1260 PASS 1260 FAIL 0 SKIP 0 XFAIL 0.

STATUS: COMPLETE round=0

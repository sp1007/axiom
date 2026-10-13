# T059 Report: Native catch-up: generics, closures, fn pointers

## Summary
Completed native catch-up for generics, closures, and function pointers across LIR, x64 backend, monomorphization, and native driver:
- In `lir.h` & `print.c`: added `AX_LIR_INST_FN_ADDR`, extended `AX_LIR_INST_CALL` with `callee_vreg` for indirect calls.
- In `lower.c`: lowered `AX_TY_FN` and `AX_TY_CLOSURE` constants to `AX_LIR_INST_FN_ADDR`; lowered closure aggregate layout (function pointer at offset 0 followed by captured variables); lowered closure and indirect calls by passing captures as leading ABI arguments and invoking `callee_vreg`; unwrapped `closure.fn_type` in entry block parameter loading and callee signature classification; added `get_place_type` to accurately compute place types for projections without evaluation side-effects; enhanced `get_fn_sym_name` to search impl and trait member functions.
- In `isel.c`: implemented `AX_LIR_INST_FN_ADDR` via LEA with symbol relocation; implemented indirect call via register `R10`.
- In `build.c`: emitted indirect register call `ax_x64_call_r`; supported function symbol LEA in `AX_X64_MI_LEA`; added fallback to construct function type signature directly from MIR body when item is unmapped; unwrapped closure `closure.fn_type` for ABI classification; fixed sizing of struct/tuple stores (`mov_mr`, `mov_rm`, `mov_rr`, `mov_mi`, `cmp`); added fallback symbol name `__ax_fn_%u` for anonymous closures.
- In `mono.c`: registered inherent and trait impl methods for monomorphization; handled anonymous closures by mangling as `__ax_fn_%u`; inserted monomorphized generic item types into `item_types`; updated call terminator `func.constant.ty` to the monomorphized callee signature to ensure correct ABI classification (e.g. pass-by-reference for closures/aggregates > 8 bytes); fixed deduplication loop to skip anonymous items (`fn.name.v == 0`); implemented receiver type matching and trait default method fallback.
- Removed all `// native-after: T059` directives across tests.

## Files changed
- bootstrap/axiom0/src/driver/build_native/build.c
- bootstrap/axiom0/src/driver/mono.c
- bootstrap/axiom0/src/lir/lir.h
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/lir/print.c
- bootstrap/axiom0/src/target/x64/isel/isel.c
- tests/run/closure/capture_modes.ax
- tests/run/closure/closure_types.ax
- tests/run/closure/fn_pointers.ax
- tests/run/closure/fn_traits.ax
- tests/run/closure/generic_fns.ax
- tests/run/closure/qa_fn_ptr_args.ax
- tests/run/closure/qa_mixed_captures.ax
- tests/run/closure/qa_move_capture.ax
- tests/run/closure/syntax.ax
- tests/run/method/builtins.ax
- tests/run/method/inherent_methods.ax
- tests/run/method/qa_run.ax
- tests/run/trait/dispatch.ax
- tests/run/trait2/test_assoc_items.ax
- tests/run/trait2/test_default_method.ax
- tests/run/trait2/test_default_override.ax
- tests/run/trait2/test_derive.ax
- tests/run/trait2/test_impl.ax
- tests/run/trait2/test_mut_view.ax
- tests/run/trait2/test_ops.ax
- tests/run/trait2/test_struct.ax
- tests/run/trait2/test_supertraits.ax
- tests/ui/trait/qa_round4_bounds.ax
- tests/ui/trait2/test_no_derive.ax

## Round 2
- Fixed architectural violation `[INV-LAYER-005]` by removing direct `#include "hir/hir.h"` from `bootstrap/axiom0/src/lir/lower.c`.
- Ran `python tools/archcheck.py`: 141 files scanned, 0 violations.
- Included `tests/run/closure/qa_fn_ptr_args.ax` in `## Files changed`.
- Clean rebuild with zero warnings/errors (`clang -Wall -Wextra -Wpedantic -Werror`).
- Verified unit tests (71/71 pass) and full test suite in `build-snap-T059`.

STATUS: COMPLETE round=2

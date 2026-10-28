# T150 Report: Port Intrinsics Table & Raw-Pointer Typing

## Summary

Ported T134's single compiler intrinsic table (`bootstrap/axiom0/src/mir/build/intrinsics.h` and `bootstrap/axiom0/src/mir/build/intrinsics.c`) and raw-pointer typing, verification, and MIR/LIR lowering into `compiler/types/`, `compiler/typeck/`, `compiler/driver/`, `compiler/mir/`, `compiler/verify/`, and `compiler/lir/`. Also optimized `verify_mir_own` in `compiler/verify/verifier.ax` so large basic-block graphs like `tests/run/intrinsics/ops_table.ax` (`bc = 2113`) verify cleanly without $O(bc^2)$ predecessor polling. Added 3 parity tests under `tests/run/parity/intrinsics/`, added a differential `AX_TYPE_UNKNOWN_INTRINSIC` check in `tests/selfhost/typeck/qa_typeck_c.ax.in`, regenerated all selfhost bundles, and shrank `tests/selfhost/obj_link_driver/known_divergent.txt` by 20 entries (from 47 entries down to 27 entries, with 0 entries added).

## Changes

1. **Single Intrinsic Table & Typecheck Validation (`compiler/types/typeck.ax`, `compiler/types/mod.ax`, `compiler/typeck/session.ax`, `compiler/driver/pipeline.ax`):**
   - Ported the 107-entry `axiom0` intrinsic catalogue (`AX_INTR_*`, `ax_intrinsic_lookup`, `ax_intrinsic_entry_arity`, `ax_intrinsic_entry_host_sym_cstr`, `ax_intrinsic_is_lowered_inline`) into `compiler/types/typeck.ax` and exported the lookup helpers via `compiler/types/mod.ax` so `typeck` and `compiler/mir/builder.ax` share a single source of truth.
   - Validated every `@intrinsic fn` item in `tc_collect_fn_sigs` (`compiler/types/typeck.ax`): unknown intrinsic names or mismatched parameter/type-parameter/return shapes emit `AX_TYPE_UNKNOWN_INTRINSIC` at `it.span` (`unknown compiler intrinsic`), matching `bootstrap/axiom0/src/typeck/checker.c:3045-3151`.
   - Passed `ResolverOutput` into `typeck_check` (`compiler/typeck/session.ax`, `compiler/driver/pipeline.ax`) so generic intrinsic call sites with turbofish or inferred type arguments (`size_of<T>()`, `align_of<T>()`, `needs_drop<T>()`, `null<T>()`, `null_mut<T>()`, `ptr_read<T>`, `ptr_write<T>`, `copy_nonoverlapping<T>`, `copy<T>`, `write_bytes<T>`, `drop_in_place<T>`) record concrete `expr_type_arg0` types on `TypeckOutput` and typecheck with concrete instantiated return/parameter types.

2. **Raw-Pointer Typing, Casts, Arithmetic, and Indexing (`compiler/types/types.ax`, `compiler/types/typeck.ax`):**
   - Supported `*const T` and `*mut T` layout (`size = 8`, `align = 8`), `TY_PTR` compatibility/coercion (`*mut T` -> `*const T`), unary dereference (`*p` as place of type `T`, mutable iff `*mut T`), pointer casts (`*const T` / `*mut T` <-> integer/pointer), and pointer arithmetic (`p + i`, `i + p`, `p - i` -> same pointer type when `i` is `usize`/`isize`; `p - q` -> `isize` when pointee types match), matching `checker.c`.

3. **MIR Intrinsic Lowering & Raw-Pointer Lowering (`compiler/mir/mir.ax`, `compiler/mir/mod.ax`, `compiler/mir/builder.ax`):**
   - Added `MIR_RVAL_INT_INTRINSIC` (`MIR_INT_WRAPPING_ADD`, `MIR_INT_WRAPPING_SUB`, `MIR_INT_WRAPPING_MUL`, `MIR_INT_WRAPPING_NEG`, `MIR_INT_COUNT_ONES`, `MIR_INT_LEADING_ZEROS`, `MIR_INT_TRAILING_ZEROS`, `MIR_INT_ROTATE_LEFT`, `MIR_INT_ROTATE_RIGHT`) and `MIR_RVAL_PTR_OFFSET` (`inbounds`, `MIR_BIN_SUB` negation when subtracting an offset) to `compiler/mir/mir.ax` with `axiom0`-matching MIR text printing.
   - Lowered all inline intrinsics in `compiler/mir/builder.ax` via the shared intrinsic table:
     - `assert`, `panic`, `unreachable` -> `MIR_TERM_ASSERT`
     - `size_of<T>()`, `align_of<T>()`, `needs_drop<T>()` -> compile-time layout/drop-glue constants
     - `null<T>()`, `null_mut<T>()` -> `0usize as *const T` / `*mut T`
     - `address_of(x)`, `address_of_mut(x)` -> `MIR_RVAL_REF` onto raw pointer local (`*const T` / `*mut T`)
     - `ptr_read<T>(src)`, `ptr_write<T>(dst, val)`, `copy_nonoverlapping<T>(src, dst, count)`, `copy<T>(src, dst, count)`, `write_bytes<T>(dst, val, count)`, `drop_in_place<T>(p)` -> alignment/null/bounds/overlap assertions + `__ax_mem_copy` / `__ax_mem_move` / `__ax_mem_set` / `MIR_STMT_DROP`, matching `bootstrap/axiom0/src/mir/build/builder.c`
     - All 90 integer wrapping/bit intrinsics across `u8..u128` / `i8..i128` -> `MIR_RVAL_INT_INTRINSIC`
     - Host intrinsics -> extern calls renamed via `ax_intrinsic_entry_host_sym_cstr` (`__ax_host_<name>`)
   - Skipped building placeholder MIR bodies for inline-lowered or host-mapped `@intrinsic fn` items (`ax_intrinsic_is_lowered_inline` or `host_sym != ""`), matching `builder.c`.
   - Lowered raw-pointer `p + i`, `i + p`, `p - i` to `MIR_RVAL_PTR_OFFSET` and `p - q` to byte-address subtraction divided by `max(size_of(T), 1)`.

4. **MIR Verification & Ownership Verification (`compiler/verify/verifier.ax`):**
   - Verified `MIR_RVAL_INT_INTRINSIC` and `MIR_RVAL_PTR_OFFSET` operands and types in `verify_mir_types`.
   - Allowed `MIR_RVAL_REF` to produce `TY_PTR` (`*const T` / `*mut T`) in addition to `TY_REF` / `TY_VIEW` / `TY_MUT_VIEW`.
   - Replaced the $O(bc^2)$ predecessor-scan dataflow loop in `verify_mir_own` with push-based successor propagation over a `dirty` block bitmap, eliminating the ~108s bottleneck on `tests/run/intrinsics/ops_table.ax` (`bc = 2113`, `lc = 2818`) while preserving exact ownership diagnostic parity.

5. **LIR Lowering (`compiler/lir/builder.ax`):**
   - Lowered `MIR_RVAL_PTR_OFFSET` (scaling element index by `size_of(T)` when `elem_sz > 1`) and `MIR_RVAL_INT_INTRINSIC` (wrapping arithmetic, `ctpop` / `ctlz` / `cttz`, `fshl` / `fshr` / masked shifts across `8`/`16`/`32`/`64`/`128`-bit integer widths) matching `bootstrap/axiom0/src/lir/lower.c`.

6. **New Parity & Selfhost Tests:**
   - `tests/run/parity/intrinsics/layout.ax`
   - `tests/run/parity/intrinsics/ptr_roundtrip.ax`
   - `tests/run/parity/intrinsics/wrapping.ax`
   - `tests/selfhost/typeck/qa_typeck_c.ax.in` (differential `AX_TYPE_UNKNOWN_INTRINSIC` check on `@intrinsic fn frobnicate(a: u32) -> u32 { 0 }` verifying exact error code and span parity against `axiom0`)

## `known_divergent.txt` Delta

`python tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py build-snap-T150/build/axiom0.exe build-snap-T150/build/e2e_tmp . --update-registry` reported:
`OK AXIOMC-E2E programs=512 equal=485 known_divergent=27 built=1932 rejected=8 obj_equal=968 exe_equal=964 run_equal=487 images=490 same_behaviour=487`

### Removed from `tests/selfhost/obj_link_driver/known_divergent.txt` (20 paths, now `EQUAL`)

- `tests/run/host/fs/dir.ax`
- `tests/run/host/fs/file_io.ax`
- `tests/run/host/fs/metadata.ax`
- `tests/run/host/heap/alloc.ax`
- `tests/run/host/io/args.ax`
- `tests/run/host/io/env.ax`
- `tests/run/host/io/write_stdout_stderr.ax`
- `tests/run/intrinsics/native_repro.ax`
- `tests/run/intrinsics/ops_table.ax`
- `tests/run/native_ptr/overlap_copy.ax`
- `tests/run/native_ptr/qa_mem_edge.ax`
- `tests/run/native_ptr/write_bytes_1mb.ax`
- `tests/run/numeric/intrinsic_ops.ax`
- `tests/run/ptr/drop_in_place.ax`
- `tests/run/ptr/layout_intrinsics.ax`
- `tests/run/ptr/linked_list.ax`
- `tests/run/ptr/mem_intrinsics.ax`
- `tests/run/ptr/oracle_null.ax`
- `tests/run/ptr/oracle_oob.ax`
- `tests/run/ptr/sum_walk.ax`

### Existing entries whose divergence class changed (0 added)

- `tests/run/closure/fn_traits.ax`: `thir	no-image` -> `thir	different-behaviour`
- `tests/run/closure/generic_fns.ax`: `thir	no-image` -> `thir	different-behaviour`
- `tests/run/mono/qa_dedup_mangling.ax`: `obj	same-behaviour` -> `backend-build	same-behaviour`

## Verification

- `python tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py build-snap-T150/build/axiom0.exe build-snap-T150/build/e2e_tmp . --update-registry`: exited `0` (`OK AXIOMC-E2E programs=512 equal=485 known_divergent=27 built=1932 rejected=8 obj_equal=968 exe_equal=964 run_equal=487 images=490 same_behaviour=487`; all 3 new `tests/run/parity/intrinsics/*.ax` programs `EQUAL`).
- `Push-Location build-snap-T150; python tools/axtest.py --compiler build/axiom0.exe -j 1; Pop-Location`: `TOTAL 2823 PASS 2823 FAIL 0 SKIP 0 XFAIL 0`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T150`: exited `0` (`0 REFUSED` lines; 91 staged files).
- `python tools/archcheck.py`: `192 files scanned, 0 violations`.

## Files changed

- compiler/driver/pipeline.ax
- compiler/lir/builder.ax
- compiler/mir/builder.ax
- compiler/mir/mir.ax
- compiler/mir/mod.ax
- compiler/typeck/session.ax
- compiler/types/mod.ax
- compiler/types/typeck.ax
- compiler/types/types.ax
- compiler/verify/verifier.ax
- tests/run/parity/intrinsics/layout.ax
- tests/run/parity/intrinsics/ptr_roundtrip.ax
- tests/run/parity/intrinsics/wrapping.ax
- tests/selfhost/abi/qa_abi_boundary_seam.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/abi/qa_abi_win64_classify.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/cap/qa_own_cap.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/drop/qa_drop_d01.ax
- tests/selfhost/drop/qa_drop_d02.ax
- tests/selfhost/drop/qa_drop_d03.ax
- tests/selfhost/drop/qa_drop_d04.ax
- tests/selfhost/drop/qa_drop_d05.ax
- tests/selfhost/drop/qa_drop_d06.ax
- tests/selfhost/drop/qa_drop_d07.ax
- tests/selfhost/drop/qa_drop_d09.ax
- tests/selfhost/drop/qa_drop_d10.ax
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/qa_drop_d12.ax
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/mir/qa_mir_text_roundtrip.ax
- tests/selfhost/obj_link_driver/known_divergent.txt
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own/qa_own_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck/qa_typeck_c.ax.in
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/types/qa_types_exhaust.ax
- tests/selfhost/types/qa_types_layout.ax
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

## Status

STATUS: COMPLETE round=0

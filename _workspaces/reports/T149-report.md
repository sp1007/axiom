# T149 Report: Port MIR Builder Parity

## Summary

Ported the remaining MIR builder and MIR printer parity rules from `bootstrap/axiom0/src/mir/build/builder.c` and `bootstrap/axiom0/src/mir/print.c` into `compiler/mir/builder.ax` and `compiler/mir/mir.ax`, added 5 hand-derived parity regression tests under `tests/run/parity/mir_builder/`, regenerated all selfhost bundles, and shrank `tests/selfhost/obj_link_driver/known_divergent.txt` by 44 entries (from 87 entries down to 43 entries).

## Changes

1. **MIR place printer paren order (`compiler/mir/mir.ax`, `mir_print_place`):**
   - Replaced reverse-order recursive `mir_print_place_inner` (which printed `((*_1)).0`) with the two-pass forward emission from `bootstrap/axiom0/src/mir/print.c:18-46` (`(*(_1)).0`), printing leading `(` for each non-deref projection and `(*(` for each `MIR_PROJ_DEREF`, followed by `_<local>` and each projection suffix in order.
   - Updated the synthetic round-trip test byte expectation in `tests/selfhost/mir/qa_mir_text_roundtrip.ax.in`.

2. **Index lvalue lowering & bounds check (`compiler/mir/builder.ax`, `mir_build_lvalue` / `mb_emit_index_bounds_check`):**
   - Reused local operands (`(MIR_OP_COPY | MIR_OP_MOVE)` with `proj_count == 0`) directly as `idx_loc` without allocating an extra copy temporary (`builder.c:901-909`).
   - Lowered array/slice/view/mut_view/str bounds checks by computing `len_loc` (`const <N>` for `TY_ARRAY`, `Len(base)` otherwise), casting `idx_loc` to `u_idx: usize`, comparing `u_idx < len_loc`, and asserting `"index out of bounds"` (`builder.c:914-974`).
   - Emitted `MIR_PROJ_DEREF` followed by `MIR_PROJ_INDEX` when indexing through `view<[T]>` / `mut_view<[T]>` (`builder.c:976-984`).

3. **`CONST_AGGREGATE` local caching (`compiler/mir/builder.ax`, `mir_build_lvalue` & `mb_build_expr_as_operand`):**
   - Cached `CONST_AGGREGATE` symbols in `b.sym_map` on first reference as a `MIR_LOCAL_CONST` local initialized in `bb0` (`builder.c:616-640`), and delegated `CONST_AGGREGATE` paths in `mb_build_expr_as_operand` to `mir_build_lvalue` (`builder.c:1027-1033`).

4. **`u32 as char` Unicode scalar value check (`compiler/mir/builder.ax`, `mir_build_expr` / `mb_emit_u32_to_char_check`):**
   - Lowered `u32 as char` casts with runtime assertions checking `op <= 0x10FFFF` and `(op < 0xD800) | (op > 0xDFFF)` with message `"invalid char value"`, matching `builder.c:2543-2625` (SPEC-03 `AXS-SEM-018`).

5. **Terminator-lowering `@intrinsic` functions (`compiler/mir/builder.ax`, `mb_has_intrinsic_attr` / `mb_item_term_intrinsic_kind`):**
   - Lowered calls to `@intrinsic fn assert(c)`, `panic([msg])`, and `unreachable()` to `MIR_TERM_ASSERT` (with messages `"assertion failed"`, `"explicit panic"` or literal message argument, and `"entered unreachable code"`), and skipped building MIR bodies for those `@intrinsic` items (`builder.c:1243-1290`, `2923-2937`).

6. **5 New Parity Tests (`tests/run/parity/mir_builder/`):**
   - `tests/run/parity/mir_builder/slice_oob.ax` (`// modes: interp native`, `// exit: 101`)
   - `tests/run/parity/mir_builder/char_cast_invalid.ax` (`// modes: interp native`, `// exit: 101`)
   - `tests/run/parity/mir_builder/for_range_sum.ax` (`// modes: interp native`, `// stdout: 145\n165\n`, `// exit: 0`)
   - `tests/run/parity/mir_builder/self_field_sum.ax` (`// modes: interp native`, `// stdout: 42\n`, `// exit: 0`)
   - `tests/run/parity/mir_builder/elem_store_through_view_drop.ax` (`// modes: interp native`, `// stdout: 2\n1\n5\n3\n77\n99\n4\n7\n6\n`, `// exit: 0`)
   - `tests/run/parity/mir_builder/qa_mir_builder_edges.ax` (`// modes: interp native`, `// stdout: 0\n55295\n57344\n1114111\n75\n87\n7733\n552\n92\n90\n91\n93\n`, `// exit: 0`)

## Removed from `tests/selfhost/obj_link_driver/known_divergent.txt` (44 paths)

- `tests/programs/expr_interp.ax`
- `tests/programs/json_parser.ax`
- `tests/programs/sorting.ax`
- `tests/programs/tokenizer.ax`
- `tests/programs/word_count.ax`
- `tests/run/array/array_basics.ax`
- `tests/run/array/array_bounds.ax`
- `tests/run/array/array_bounds_neg.ax`
- `tests/run/array/qa_array_bounds_write.ax`
- `tests/run/array/qa_nested_array_bounds.ax`
- `tests/run/array/qa_nested_arrays.ax`
- `tests/run/comptime/array_len.ax`
- `tests/run/comptime/qa_scalar_const_str_utf8.ax`
- `tests/run/comptime/qa_table_struct_str.ax`
- `tests/run/comptime/qa_table_u8_loop.ax`
- `tests/run/comptime/table_str.ax`
- `tests/run/comptime/table_struct.ax`
- `tests/run/comptime/table_u8_256.ax`
- `tests/run/drop/array_elem_assign_drop.ax`
- `tests/run/drop/qa_t141_r1_assign_places.ax`
- `tests/run/ffi/write_file.ax`
- `tests/run/host/fs/clock.ax`
- `tests/run/host/io/invalid_handle.ax`
- `tests/run/intrinsics/assert_false.ax`
- `tests/run/intrinsics/assert_true.ax`
- `tests/run/intrinsics/panic_abort.ax`
- `tests/run/intrinsics/panic_in_branch.ax`
- `tests/run/native_const/identical_tables.ax`
- `tests/run/native_const/qa_table_str_empty_and_multitables.ax`
- `tests/run/native_const/table_4kb.ax`
- `tests/run/native_str/qa_hello_empty.ax`
- `tests/run/numeric/cast_char.ax`
- `tests/run/numeric/panic_char_110000.ax`
- `tests/run/numeric/panic_char_d800.ax`
- `tests/run/numeric/qa_cast_char_edges.ax`
- `tests/run/numeric/qa_char_ordering.ax`
- `tests/run/numeric/qa_panic_char_dfff.ax`
- `tests/run/ptr/arena_align.ax`
- `tests/run/ptr/oracle_misaligned.ax`
- `tests/run/slice/coerce.ax`
- `tests/run/slice/qa_slice_mutate.ax`
- `tests/run/slice/qa_slice_mutate_2.ax`
- `tests/run/slice/sum.ax`
- `tests/run/str/qa_hello_empty.ax`

## Verification

- All 22 `T149` plan table entries in `_workspaces/reports/plan-axiomc-divergence.md` produce identical `inspect --emit=mir` (with `type#<n>` normalized) and `EQUAL` (`obj O0`, `exe O0`, `obj O1`, `exe O1`, `run_equal`) under `axiomc_e2e_oracle.py`.
- `python tools/axtest.py --compiler build/axiom0.exe -j 1 run/parity/mir_builder selfhost/drop/drop_oracle.test selfhost/obj_link_driver bundles_current`: `TOTAL 58 PASS 58 FAIL 0 SKIP 0 XFAIL 0`.
- Selfhost suites `selfhost/mir`, `selfhost/own_mir_verify`, `selfhost/drop`, `selfhost/verify`, `selfhost/lir`, `selfhost/interp_opt`, `selfhost/backend`, `selfhost/driver`: 100% PASS (`FAIL 0`).
- `python tools/archcheck.py`: `192 files scanned, 0 violations`.

## Files changed

- compiler/mir/builder.ax
- compiler/mir/mir.ax
- tests/run/parity/mir_builder/char_cast_invalid.ax
- tests/run/parity/mir_builder/elem_store_through_view_drop.ax
- tests/run/parity/mir_builder/for_range_sum.ax
- tests/run/parity/mir_builder/qa_mir_builder_edges.ax
- tests/run/parity/mir_builder/self_field_sum.ax
- tests/run/parity/mir_builder/slice_oob.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/backend/gen_backend_tests.py
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
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
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
- tests/selfhost/mir/qa_mir_text_roundtrip.ax.in
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
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

## Status

STATUS: COMPLETE round=0

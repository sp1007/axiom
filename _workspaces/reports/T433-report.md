# T433 Report — Baseline fix: missing diagnostics & int128 typeck

## Summary
Resolved all 7 baseline failure IDs assigned to `T433` in `_workspaces/baseline-failures.txt`, restored the spec-mandated diagnostics (`SPEC-30` `REQ-CONC-004`, `SPEC-11` `view` is not `Share`, `SPEC-03` `AXS-SEM-037`, `SPEC-40` `int128`), added 5 focused regression tests, regenerated all 14 affected selfhost test bundles (56 `.ax` bundle files), rebuilt Stage-1 (`axiomc1.exe`) and Stage-2 (`axiomc2.exe` / `axiomc2_O1.exe` / `axiomc.exe`), and verified `0` new failures across all affected suites and selfhost `bundles_current.test` checks.

## Root Causes & Fixes for the 7 Baseline IDs

1. **`typeck/int128/int128_literals_and_methods.test` (`SPEC-40`)**:
   - **Breaking commit**: `T406` (`fa86bbfc`) injected bare `@derive(Copy) pub enum Ordering` into `std/core/prelude.ax` and added unguarded synthetic `10007u32` / `10008u32` auto-trait symbol checks in `compiler/traits/solver.ax`, colliding with local `@lang("Ordering") enum Ordering` and trait symbol IDs in `int128_literals_and_methods.test`.
   - **Resolution**: Restored by `T432` (`a4d158d9`, moving `Ordering` out of `std/core/prelude.ax` and guarding synthetic `10007u32`/`10008u32` checks in `compiler/traits/solver.ax`) and `T452` (`e0637c50`). Verified passing under rebuilt Stage-2 `axiomc2.exe` (`--no-cache -v -j 2`) and removed from `_workspaces/baseline-failures.txt`.

2. **`ui/struct/unknown_field.ax` (`AX_TYPE_UNKNOWN_FIELD`)**:
   - **Breaking commit**: `T406` (`fa86bbfc`) / `T088` (`e969c207`) caused implicitly loaded `<std>` prelude/derive items to leak diagnostics into user compilation units before reaching struct field checking.
   - **Resolution**: Restored by `T434` (`bda3bb63`) and `T432` (`a4d158d9`). Verified passing under rebuilt Stage-2 `axiomc2.exe` (`--no-cache -v -j 2`) and removed from `_workspaces/baseline-failures.txt`.

3. **Group A — `run/parse/terminator_one_line_items.ax` (`AX_TYPE_UNKNOWN` in `<std>/future/block_on.ax:18:17`)**:
   - **Breaking commit**: `T088` (`e969c207`), which added implicitly loaded `<std>/future/block_on.ax` containing `fn drop_val<T>(val: T)` and `pub fn block_on<F: Future<Output = T>, T>(mut fut: F) -> T`.
   - **Root cause**: `terminator_one_line_items.ax` declares top-level `struct S { x: i32 } ; struct T { y: i32 }` on line 7. In `compiler/types/typeck.ax`, `register_item_sig` did not populate `thir.symbol_types` for `HIR_ITEM_FN` generic parameters, so `lookup_path_type` fell through to `lookup_path_type_by_name`. In `lookup_path_type_by_name`, the global `(*cx.hir).items` loop ran **before** `cx.current_fn` / `cx.current_impl` `generic_params`. Consequently, any user-declared top-level `struct T` shadowed the generic type parameter `T` inside `<std>/future/block_on.ax`, giving `drop_val<T>(val: T)` the parameter type `struct T` instead of `TY_PARAM(0)` and leaving `drop_val(fut)`'s freshly instantiated type variable unconstrained (`AX_TYPE_UNKNOWN`).
   - **Fix**: Added `tc_resolve_generic_param_sym` in `lookup_path_type` (matching active `cx.current_fn` / `cx.current_impl` generic parameter `SymbolId`s) and moved `cx.current_fn` / `cx.current_impl` `generic_params` resolution ahead of the global `(*cx.hir).items` scan in `lookup_path_type_by_name` when `path.generic_args == 0`.
   - **Regression test**: `tests/ui/struct/struct_t_shadowing_std_generics.ax` (`// test: run`, `// stdout: struct_t_shadow_ok 42\n`).

4. **Group B — `run/slice/qa_slice_inverted_panic.ax` (`AX_VERIFY_TYPE_MISMATCH` on `let sub = v[3..2];`)**:
   - **Breaking commit**: `T402` (`b804dfc6`), which added a compile-time `cs > ce` check on `MIR_PROJ_SUB_SLICE` inside `verify_mir_cap` (`compiler/verify/verifier.ax:3628-3648`) that emitted `AX_VERIFY_TYPE_MISMATCH` (`"mutable borrow of immutable local in MIR"`).
   - **Root cause**: Per `SPEC-03` `AXS-SEM-037`, slice range indexing with inverted bounds (`start > end`) is a runtime bounds panic (`exit: 101` via the `MIR_TERM_ASSERT` emitted by `mb_emit_range_bounds_check` in `compiler/mir/builder.ax`), not a compile-time MIR capability verification error.
   - **Fix**: Removed the bogus `cs > ce` compile-time rejection in `verify_mir_cap` (`compiler/verify/verifier.ax`) so `v[3..2]` and `mv[4..1]` verify cleanly and panic at runtime with exit code `101` in `[interp]`, `[native]`, and `[native-O1]`.
   - **Regression test**: `tests/ui/struct/inverted_array_and_mut_slice_panic.ax` (`// test: run`, `// exit: 101`).

5. **Group C — Concurrency & Thread-Local UI Diagnostics (`SPEC-30` `REQ-CONC-004`, `SPEC-11`)**:
   - **`conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax`**:
     - **Breaking commit**: `T413` (`7a8ef713`), which added `check_thread_local_items` and `typeck_eval_tls_aggregate` in `compiler/types/typeck.ax`.
     - **Root cause**: `typeck_eval_tls_aggregate` only recognized `LocalKey` call initializers (`init_fn`), returning `false` for `@thread_local static OK_TLS_CELL: Cell = Cell { val: 99 };` (line 35) and emitting a spurious `AX_TYPE_INVALID_TLS_DECL` during `STAGE_TYPECK`. Because `STAGE_TYPECK` errors halt the pipeline before `STAGE_OWN` (`spec/diagnostics.md` `AXD-044`), `compiler/own/unsafe.ax` never ran to emit `AX_CONC_UNSYNC_STATIC` (lines 29, 30, 31, 50, 51) and `AX_CONC_SHARED_MUT` (line 62).
     - **Fix**: Added `tc_write_u128_le`, `tc_align_up_usize`, and recursive `tc_eval_tls_const_bytes` in `compiler/types/typeck.ax` (invoked from `typeck_eval_tls_aggregate` when `fn_sym_v == 0u32`), supporting constant struct, tuple, array, and scalar/block initializers on `@thread_local static` items while still rejecting non-const runtime call initializers (`compute()`) with `AX_TYPE_INVALID_TLS_DECL`.
   - **`ui/concurrency/data_race/unsync_static_and_unsafe_reentry.ax` & `ui/concurrency/data_race/view_not_share_rejected.ax`**:
     - **Breaking commit**: `T090` (`564b119c`), which extended `verify_closure_at_boundary` in `compiler/types/typeck.ax` (`STAGE_TYPECK`) from `boundary_kind == 1u8` (`spawn`) to `boundary_kind == 4u8` (`spawn_scoped` / `Scope.spawn`).
     - **Root cause**: When a scoped task captured or received a shared `view<T>` (`TY_VIEW`) where `T: !Share`, `typeck.ax` emitted `AX_CONC_CAPTURE_NOT_SEND` in `STAGE_TYPECK` instead of deferring to `STAGE_OWN` (`compiler/own/unsafe.ax`), which both emitted the wrong diagnostic code (`SPEC-30` `AXS-CONC-031` / `AXS-CONC-050` mandates `AX_CONC_VIEW_NOT_SHARE` for concurrent `READ`/`READ` sharing of `view<T>` where `T: !Share`) and blocked `STAGE_OWN` from running on the rest of the file.
     - **Fix**: In `verify_closure_at_boundary` and `scan_spawn_boundaries_expr` (`compiler/types/typeck.ax`), when `boundary_kind == 4u8` (`spawn_scoped` / `Scope.spawn`) and the captured/passed type has `kind == TY_VIEW`, skip emitting `AX_CONC_CAPTURE_NOT_SEND` in `STAGE_TYPECK` so `STAGE_OWN` (`compiler/own/unsafe.ax`) emits `AX_CONC_VIEW_NOT_SHARE` (while keeping `AX_CONC_CAPTURE_NOT_SEND` in `STAGE_TYPECK` for non-view `!Send` captures in `spawn_scoped`). In `compiler/own/unsafe.ax`, added `conc_expr_base_shared_view_ty`, `reported_vns` per-expression deduplication, and `suppress_branch_diags` during sibling-spawn re-collection in `unsafe_check_block` so projections of `Share` scalar fields (`(*vst).code`) out of a shared `view<UnsyncState>` (`UnsyncState: !Share`) also emit `AX_CONC_VIEW_NOT_SHARE` exactly once.
   - **Regression tests**:
     - `tests/ui/concurrency/data_race/tls_struct_init_and_scoped_view_not_share.ax` (`// test: ui`)
     - `tests/ui/concurrency/data_race/scoped_non_send_move_rejected.ax` (`// test: ui`)
     - `tests/ui/concurrency/data_race/tls_const_struct_init_run.ax` (`// test: run`, `// stdout: tls_agg_ok 99 15 30\n`)

## Build, Verification & Mutation Proof (`build-snap-T433`)
- **Stage-1 (`axiomc1.exe`)**: `26127360` bytes, `sha256=098701386e5fad35c894e837e44aeeb7b9b44c3d9510e5be53c9fa876b7eb848` (copied to `build/axiomc1.exe`).
- **Stage-2 (`--stage 2`, O1, `axiomc2.exe` / `axiomc2_O1.exe` / `axiomc.exe`)**: `8108544` bytes, `sha256=3518e4cd7d49c399622547f7a2feea4261431adff0a31022680ae9fdaa43dc71` (copied to `build/axiomc2.exe`, `build/axiomc2_O1.exe`, and `build/axiomc.exe`).
- **7 `T433` target IDs + 5 new regression tests (`--no-cache -v -j 2`, `axiomc2.exe`)**:
  - `TOTAL 22 PASS 22 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- **1-byte mutation proof on new `run` regression tests (`-j 2`)**:
  - Temporarily mutating 1 byte of `// stdout:` in `tls_const_struct_init_run.ax` (`30` -> `31`) and `struct_t_shadowing_std_generics.ax` (`42` -> `43`), and `// exit:` in `inverted_array_and_mut_slice_panic.ax` (`101` -> `100`), caused `[native]` and `[native-O1]` to FAIL as expected (`rc=1`, `WEAK-NATIVE 0`); restored and re-verified `PASS`.
- **All 31 `selfhost/**/bundles_current.test` + affected suites (`ui/concurrency`, `conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax`, `ui/struct`, `run/slice`, `run/parse`, `typeck/int128`, `own`, `verify`) under `build-snap-T433/build/axiomc2.exe` (`-j 2`, `--baseline _workspaces/baseline-failures.txt`)**:
  - `TOTAL 290 PASS 283 FAIL 2 SKIP 5 XFAIL 0`, `BASELINE OK` (`0` new failures; the 2 failed mode entries are pre-existing baseline entry `selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` owned by `T445`).
- **Selfhost generators & hygiene checks**:
  - All 36 `tests/selfhost/**/gen_*.py --check`: exit `0`, zero `DIFFERS`.
  - `python tools/archcheck.py --root build-snap-T433`: `229 files scanned, 0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T433`: `0 REFUSED`, `0 UNLISTED`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

## Round 1
- Added `// stdout: 42\n` and `print_int(...); print("\n");` to `tests/ui/struct/nested_struct_qa.ax` and `tests/ui/struct/nested_tuple_qa.ax` so `taskgate.py` records non-trivial native evidence (`WEAK-NATIVE 0`) on both files in `[native]` and `[native-O1]`.

## Files changed
- _workspaces/baseline-failures.txt
- compiler/own/unsafe.ax
- compiler/types/typeck.ax
- compiler/verify/verifier.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
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
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
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
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/ui/concurrency/data_race/scoped_non_send_move_rejected.ax
- tests/ui/concurrency/data_race/tls_const_struct_init_run.ax
- tests/ui/concurrency/data_race/tls_struct_init_and_scoped_view_not_share.ax
- tests/ui/struct/inverted_array_and_mut_slice_panic.ax
- tests/ui/struct/nested_struct_qa.ax
- tests/ui/struct/nested_tuple_qa.ax
- tests/ui/struct/struct_t_shadowing_std_generics.ax

STATUS: COMPLETE round=1

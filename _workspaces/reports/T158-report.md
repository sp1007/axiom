# T158 Report — AX0-FIX-07: Language `Drop` Identified by Resolution (`AXS-DROP-008`)

## Summary

Implemented `SPEC-12` `AXS-DROP-008` (`ADR-0036` §5, `ADR-0034` §2 and §6) across both the C bootstrap (`bootstrap/axiom0`) and the Axiom self-hosted compiler (`compiler/`): an `impl P for T` block declares the language destructor of `T` if and only if its trait path `P` resolves to the prelude `Drop` lang item rather than a user-defined trait that happens to end in `Drop`.

## Root Cause Analysis

Before `T158`, language `Drop` detection relied on syntactic string matching across six compiler sites, with an additional disagreement between HIR post-processing and downstream stages:

1. **HIR post-processing (`bootstrap/axiom0/src/driver/pipeline.c` `stage_hir` and `compiler/hir/lower.ax` `hir_postprocess_items`)** checked only `strcmp(tname, "Drop") == 0` on `impl->trait_path->path.name` (with `generic_args == NULL`). Because parser/HIR lowering stores only the final segment of a multi-segment path in `HirPath.name`, both `impl Drop for S` and `impl traits.Drop for S` had `path.name == "Drop"` and had their `drop` method renamed to `S_drop` in HIR.
2. **Type checking (`bootstrap/axiom0/src/types/typeck.c` and `compiler/types/typeck.ax`)** and **MIR drop elaboration (`bootstrap/axiom0/src/mir/drop/drop.c` and `compiler/mir/drop.ax`)** checked `strcmp(tname, "Drop") == 0 || (len > 5 && strcmp(tname + len - 5, ".Drop") == 0)`, treating any trait whose name or qualified path ended in `Drop` as the language destructor:
   - `typeck` renamed its `S_drop` method to `S$drop` (`ADR-0034` reserved `$` destructor symbol) and registered `ax_type_registry_set_has_drop` (making `S` non-`Copy` / linear).
   - `mir/drop` scheduled automatic scope-exit `S$drop` calls and synthetic drop glue for `S`.

Consequently, implementing a user-defined trait `traits.Drop` (or a module-local or `use`-imported `Drop` that shadows the prelude) corrupted method resolution, stripped `Copy` semantics from the implementing type, and injected unintended scope-exit destructor calls.

## Implementation Details

### Language `Drop` Resolution Predicate (`AXS-DROP-008`)

In Axiom v0.1, the prelude `Drop` lang item has no module path and is reachable only by the bare identifier `Drop` when unshadowed in the `impl` item's module. An `AX_HIR_ITEM_IMPL` item is the language `Drop` impl iff:

1. `impl->trait_path` is a non-null `AX_HIR_TYPE_PATH` with `generic_args == NULL` and `path.name == "Drop"`.
2. `impl->trait_path->path.span` is a bare single-segment `Drop` reference: when `span.file.v != 0`, `span.end - span.start == 4` (a qualified path such as `traits.Drop` has a `HirPath.span` covering all segments from the first identifier to the last, so its span length is strictly greater than `4`; when `db` is available in `axiom0`, the source slice is additionally checked against `"Drop"`).
3. No item in `hir->items` belonging to the same `module_path` as `impl` shadows `Drop` in module scope:
   - No `AX_HIR_ITEM_TRAIT`, `AX_HIR_ITEM_STRUCT`, `AX_HIR_ITEM_ENUM`, or `AX_HIR_ITEM_TYPE_ALIAS` in that module has `name == "Drop"`.
   - No `AX_HIR_ITEM_USE` in that module has a `HirUseTree` leaf binding the name `"Drop"` (either via `alias == "Drop"` or, when `alias` is empty and `subtrees == NULL`, via the last segment of `use_tree->path` being `"Drop"`).

### Code Changes

- **`bootstrap/axiom0/src/mir/drop/drop.h` & `bootstrap/axiom0/src/mir/drop/drop.c`**:
  - Declared and implemented `ax_hir_impl_is_lang_drop(const AxHirItem *impl, const AxHirFile *hir, const AxStrInterner *interner, const AxSourceDb *db)`.
  - Replaced `is_drop_trait_name` in `ax_find_drop_impl_fn` with `ax_hir_impl_is_lang_drop(it, hir, interner, NULL)`.
- **`bootstrap/axiom0/src/driver/pipeline.c`**:
  - Included `"mir/drop/drop.h"` and replaced the raw `strcmp(tname, "Drop") == 0` check in `stage_hir` with `ax_hir_impl_is_lang_drop(it, &st->hir, &st->interner, &st->db)`.
- **`bootstrap/axiom0/src/types/typeck.c`**:
  - Added `tc_impl_is_lang_drop(const AxHirFile *hir, const AxHirItem *impl, const AxStrInterner *str_in, const AxSourceDb *db)` (respecting the `archcheck.py` layer boundary where `types` is layer 6 and `mir` is layer 8) and replaced all three `.Drop` suffix checks in `ax_typeck_with_evaluator`.
- **`compiler/hir/lower.ax`**:
  - Added `hir_name_is_drop`, `hir_use_tree_binds_drop`, `hir_module_path_eq`, and `pub fn hir_impl_is_lang_drop(items: *mut HirItem, impl_item: *mut HirItem, interner: view<StrInterner>) -> bool`.
  - Updated `hir_postprocess_items` to gate `S_drop` renaming on `hir_impl_is_lang_drop(hf.items, it, view(*interner))`.
- **`compiler/mir/drop.ax`**:
  - Added `drop_name_is_drop`, `drop_use_tree_binds_drop`, `drop_module_path_eq`, and `drop_impl_is_lang_drop`, and updated `drop_impl_is_drop_for` to call `drop_impl_is_lang_drop(items, it, interner)` instead of `drop_is_drop_trait_name`.
- **`compiler/types/typeck.ax`**:
  - Added `tc_name_is_drop`, `tc_use_tree_binds_drop`, `tc_module_path_eq`, and `tc_impl_is_lang_drop(items: *mut HirItem, impl_item: *mut HirItem, interner: view<StrInterner>) -> bool`.
  - Replaced `tc_is_drop_trait_name` in both `tc_mangle_drop_impls` and `typeck_pass1b_and_2` (`has_drop` registration).

### Regenerated Selfhost Bundles and Generators

Updated the reference bundle and selfhost generator patch hooks so all selfhost bundles embed the updated `compiler.hir.lower`, `compiler.mir.drop`, and `compiler.types.typeck` modules:

- **Reference bundle updated**:
  - `tests/selfhost/lir/qa_lir_from_ax_a.ax` (`module compiler.hir.lower` section updated with `hir_impl_is_lang_drop`).
- **Generators updated and executed**:
  1. `python tests/selfhost/backend/gen_backend_tests.py` (patch updated for `tc_impl_is_lang_drop`) -> regenerated:
     - `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
     - `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
     - `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
     - `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
     - `tests/selfhost/backend/qa_backend_edge.ax`
     - `tests/selfhost/backend/qa_backend_unit.ax`
  2. `python tests/selfhost/driver/gen_driver_tests.py` (patch updated for `tc_impl_is_lang_drop`) -> regenerated:
     - `tests/selfhost/driver/qa_driver_commands_a.ax`
     - `tests/selfhost/driver/qa_driver_commands_b.ax`
     - `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
     - `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
  3. `python tests/selfhost/drop/gen_drop_tests.py bundles` -> regenerated:
     - `tests/selfhost/drop/qa_drop_d01.ax`
     - `tests/selfhost/drop/qa_drop_d02.ax`
     - `tests/selfhost/drop/qa_drop_d03.ax`
     - `tests/selfhost/drop/qa_drop_d04.ax`
     - `tests/selfhost/drop/qa_drop_d05.ax`
     - `tests/selfhost/drop/qa_drop_d06.ax`
     - `tests/selfhost/drop/qa_drop_d07.ax`
     - `tests/selfhost/drop/qa_drop_d09.ax`
     - `tests/selfhost/drop/qa_drop_d10.ax`
     - `tests/selfhost/drop/qa_drop_d11.ax`
     - `tests/selfhost/drop/qa_drop_d12.ax`
  4. `python tests/selfhost/interp/gen_interp_tests.py bundles` -> regenerated:
     - `tests/selfhost/interp/qa_interp_exec_a.ax`
     - `tests/selfhost/interp/qa_interp_exec_b.ax`
     - `tests/selfhost/interp/qa_interp_unit.ax`
  5. `python tests/selfhost/interp_opt/gen_interp_opt_tests.py` (patch updated for `tc_impl_is_lang_drop`) -> regenerated:
     - `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax`
     - `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax`
     - `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax`
     - `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax`
     - `tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax`
     - `tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax`
     - `tests/selfhost/interp_opt/qa_interp_opt_unit.ax`
  6. `python tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` -> regenerated:
     - `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
     - `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`
  7. `python tests/selfhost/opt/gen_opt_tests.py bundles` -> regenerated:
     - `tests/selfhost/opt/qa_opt_pipeline.ax`
     - `tests/selfhost/opt/qa_opt_unit.ax`
  8. `python tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py` (patch updated for `tc_impl_is_lang_drop`) -> regenerated:
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax`
     - `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax`
  9. `python tests/selfhost/verify/gen_verify_tests.py bundles` -> regenerated:
     - `tests/selfhost/verify/qa_verify_mir.ax`
     - `tests/selfhost/verify/qa_verify_pipeline.ax`

## Verification Results

1. **GCC & Clang Builds (`build-snap-T158`)**:
   - `cmake -B build-snap-T158/build -S build-snap-T158/bootstrap/axiom0 -G Ninja -DCMAKE_C_COMPILER=gcc -DCMAKE_BUILD_TYPE=Debug` + `cmake --build build-snap-T158/build --clean-first`: **0 warnings, exit 0**.
   - `cmake -B build-snap-T158/build-clang -S build-snap-T158/bootstrap/axiom0 -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Debug` + `cmake --build build-snap-T158/build-clang --clean-first`: **0 warnings, exit 0**.
2. **Architecture Check**:
   - `python tools/archcheck.py --root build-snap-T158`: `archcheck: OK (192 files scanned, 0 violations)`.
3. **New Parity Tests (`tests/run/parity/drop_trait/`)**:
   - `tests/run/parity/drop_trait/user_trait_named_drop.ax` (`interp`, `native`, `e2e` via `axiomc_e2e`): PASS (`custom drop 1`, `custom drop 2`, `done`, `S` remains `Copy`-able, no scope-exit destructor call).
   - `tests/run/parity/drop_trait/lang_drop_still_works.ax` (`interp`, `native`, `e2e`): PASS (`in scope`, `lang drop`, `after scope`).
   - `tests/run/parity/drop_trait/shadowing_trait_drop.ax` (`interp`, `native`, `e2e`): PASS (module-local `trait Drop` shadows prelude `Drop`; sibling module `other` without shadowing still invokes prelude `Drop` at scope exit).
   - `tests/run/parity/drop_trait/imported_trait_drop.ax` (`interp`, `native`, `e2e`): PASS (`use traits.Drop` shadows prelude `Drop`; no scope-exit destructor call).
4. **Full Test Suite (`build-snap-T158`)**:
   - `python build-snap-T158/tools/axtest.py --compiler build-snap-T158/build/axiom0.exe --root build-snap-T158 -j 2`:
     **`TOTAL 2683 PASS 2683 FAIL 0 SKIP 0 XFAIL 0`** (including `selfhost/axiomc_e2e/axiomc_e2e.test`, `run/drop/**`, `run/mangle/drop_symbols.test`, `ui/drop/**`, and all `selfhost/**` suites; `known_divergent.txt` unchanged).

## Files changed

- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/mir/drop/drop.c
- bootstrap/axiom0/src/mir/drop/drop.h
- bootstrap/axiom0/src/types/typeck.c
- compiler/hir/lower.ax
- compiler/mir/drop.ax
- compiler/types/typeck.ax
- tests/run/parity/drop_trait/imported_trait_drop.ax
- tests/run/parity/drop_trait/lang_drop_still_works.ax
- tests/run/parity/drop_trait/shadowing_trait_drop.ax
- tests/run/parity/drop_trait/user_trait_named_drop.ax
- tests/selfhost/backend/gen_backend_tests.py
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/gen_driver_tests.py
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
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py
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

# T432 Report — Baseline fix: prelude/std regressions after the P11 prelude additions

## Summary & ADR-0041 §2 D4 Resolution
- **Eliminated implicit prelude bare-name collisions (`ADR-0041 §2 D4`, `SPEC-31`, `SPEC-33`)**:
  - Removed the duplicate `Ordering`, `CasResult<T>`, and `Atomic<T>` declarations (and their `@derive(Copy)` attributes) from `std/core/prelude.ax`.
  - `std/sync/atomic.ax` (`std.sync.atomic`) now holds the single canonical definition of atomic memory `Ordering`, `CasResult<T>`, `Atomic<T>`, `Atomic*` type aliases, `fence`, `compiler_fence`, `spin_loop_hint`, and `is_lock_free`.
  - `std/core/cmp.ax` (`std.core.cmp`) holds comparison `Ordering`.
  - `std/core/prelude.ax` retains only `Option<T>`, `Result<T, E>`, `prelude_loaded()`, and the async lang items (`Poll<T>`, `RawWaker`, `RawWakerVTable`, `Waker`, `Context`, `Future`).
  - Neither `std.sync.atomic.Ordering` nor `std.core.cmp.Ordering` is injected into every file's bare-name prelude scope; `compiler/driver/pipeline.ax` loads `std/sync/atomic.ax` and `std/core/cmp.ax` on demand when referenced (preserving `--dep-file` minimal input invariants), while `compiler/resolve/resolver.ax` exposes non-colliding `Atomic` / `CasResult` / `Atomic*` / fence symbols when `std.sync.atomic` is loaded and keeps `Ordering` strictly module-scoped.

## Root Causes & Fixes for the 5 Baseline IDs
1. **`modules/prelude_implicit` (`AX_LINK_UNDEFINED_SYMBOL: prelude_loaded`)**:
   - **Root cause**: In `compiler/driver/pipeline.ax` (`driver_build_package_exe`), emitting per-module `.obj` files in multi-file package builds passed `include_std_weak = false` for every file including the entry module (`main.ax`), so referenced `<std>/core/prelude.ax` functions (`prelude_loaded`) were resolved and type-checked but never emitted into any object file.
   - **Fix**: Passed `include_std_weak = is_entry_mod` when emitting the entry module `.obj` in `driver_build_package_exe` so `<std>` weak definitions are emitted once into the package entry object.
2. **`typeck/async/async_basic_pos.ax` (`AX_TRAIT_AMBIGUOUS_METHOD` in `std/future/block_on.ax:16` + THIR dump hygiene)**:
   - **Root cause A (trait method ambiguity & auto-trait symbol collision)**: `find_method` in `compiler/traits/solver.ax` matched all `HIR_ITEM_TRAIT` items in HIR for a `TY_PARAM` receiver without checking active `fn`/`impl` generic bounds (`F: Future`), and hardcoded synthetic `10007u32`/`10008u32` (`Send`/`Share`) checks lacked `tn_len == 0` / `itn_len == 0` guards when real `<std>` traits (`Ord`, `PartialEq`) were assigned those symbol IDs.
   - **Root cause B (local `@lang` override & THIR pre-lowering fidelity)**: `compiler/mir/async_lower.ax` picked `<std>/core/prelude.ax` lang items before local `@lang("poll")` / `@lang("future")` declarations and hardcoded `Context` instead of reading `Future.poll`'s 2nd parameter pointee type; additionally, `EMIT_THIR` in `compiler/driver/pipeline.ax` rendered THIR *after* `STAGE_OWN` (`mir_lower_async_body`) mutated `is_async = false` and linked untyped `__ax_poll_*` MIR-lowering items into HIR.
   - **Fix**: Added `find_method_in_scope` + `ty_param_allows_trait` (matching `param_index` positionally and checking supertraits) and guarded synthetic `10007u32`/`10008u32` checks in `compiler/traits/solver.ax`; prioritized user `@lang` items over `<std>` prelude fallbacks and extracted `cx_ty_v` dynamically in `compiler/mir/async_lower.ax`; rendered THIR right after `STAGE_TYPECK` while still running `STAGE_OWN` verification in `compiler/driver/pipeline.ax`; and updated `tests/typeck/async/async_basic_pos.thir` (removing the two leaked T406 `@derive(Copy)` items and reflecting typed `async fn` bodies preserved since T417).
3. **`std/core/qa_generic_method.ax`**:
   - **Root cause**: Legacy negative UI test (`// test: ui`) asserting an obsolete `typeck.c` limitation (`//~ ERROR AX_TYPE_UNKNOWN_FIELD` when calling inherent methods on generic nominal types `MyOpt<i32>`), which now resolves and executes cleanly.
   - **Fix**: Converted `tests/std/core/qa_generic_method.ax` into a positive `// test: run` (`modes: interp native`, `stdout: generic_method_ok\n`).
4. **`run/trait2/test_derive.ax`**:
   - **Root cause**: Used retired `:=` bindings and `::` path separators (`SPEC-02`), and user trait/type declarations collided with implicit `<std>` symbols because `sym_is_prelude_item` in `compiler/resolve/resolver.ax` only checked `std.core.prelude` instead of all `<std>` modules.
   - **Fix**: Generalized `sym_is_std_item` shadowing in `compiler/resolve/resolver.ax` and migrated `tests/run/trait2/test_derive.ax` to canonical `=` and `.` syntax.
5. **`std/channel/check_channel_bundles.test`**:
   - **Root cause**: Generated `tests/std/channel/channel_*.ax` bundles embedded the pre-T432 `std/core/prelude.ax` text.
   - **Fix**: Regenerated `tests/std/channel/channel_*.ax` via `python tests/std/channel/gen_tests.py` (`--check` exits 0).

## Multi-Segment Qualified Enum Paths & Regression Test
- Added `recover_postfix_chain_target` in `compiler/resolve/resolver.ax` so multi-segment module-qualified variant expressions (`std.core.cmp.Ordering.Less`, `std.sync.atomic.Ordering.Acquire`) resolve cleanly across module and type namespaces.
- Updated `tc_match_check_exhaust_bool_or_enum` in `compiler/types/typeck.ax` to match enum variants by resolved `SymbolId` in addition to path segment names.
- Added tuple receiver arity matching in `compiler/traits/solver.ax` and generic trait-impl parameter counting (`mb_count_generic_params_in_hir`, excluding `lang("drop")` and inherent impls) plus auto-borrowed receiver source-type deduction in `compiler/mir/builder.ax` so uninstantiated generic trait impls in `<std>/core/cmp.ax` (`Ord`/`PartialEq` for tuples) are not emitted unmonomorphized when `<std>/core/cmp.ax` is loaded.
- Added `tests/typeck/async/ordering_cmp_and_atomic_paths.ax` (`// test: run`, `// modes: interp native`, `// stdout: cmp_and_atomic_ordering_ok\n`), exercising both `std.core.cmp.Ordering` and `std.sync.atomic.Ordering` by path in the same compilation unit.
- Removed all 5 `T432` entries from `_workspaces/baseline-failures.txt` and added `compiler/mir/async_lower.ax` to `T432` `locks:`.

## Build & Verification (`build-snap-T432`)
- **Stage-1 (`axiomc1.exe`)**: `26072064` bytes, `sha256=46b5dadbb1a183d24d215c6dcf47bfbf8cd8c52e88aa73a9244a801414fcead6` (copied to `build/axiomc1.exe`).
- **Stage-2 (`--stage 2`, O1, `axiomc2.exe` / `axiomc.exe`)**: `8078848` bytes, `sha256=c7babe3007b84b53fe3f356278ecce0c9bcf0fa757a7d1c632e8f10967985315` (copied to `build/axiomc2.exe`, `build/axiomc2_O1.exe`, and `build/axiomc.exe`).
- **Target & regression tests (`--no-cache`, `-j 2`, `axiomc2.exe`)**:
  - `modules/prelude_implicit`, `typeck/async/async_basic_pos.ax`, `std/core/qa_generic_method.ax`, `run/trait2/test_derive.ax`, `std/channel/check_channel_bundles.test`, and `typeck/async/ordering_cmp_and_atomic_paths.ax` (14 mode entries): `TOTAL 14 PASS 14 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`, `BASELINE OK`.
- **Non-selfhost affected suites + all `selfhost/**/bundles_current.test` (`-j 2`, `axiomc2.exe`, `--baseline build-snap-T432/_workspaces/baseline-failures.txt`)**:
  - `run/atomics/`, `mir/atomics/`, `ui/concurrency/atomics/`, `std/async/`, `conformance/p11/`, `modules/`, `typeck/`, `parse/`, `resolve/`, `hir/`, `std/core/`, `run/trait2/`, `std/channel/`, `driver/dep_file/`, `ui/parse/`, `ui/resolve/`, `ui/hir/`, `ui/async/`, `run/mono/`, and all 31 `selfhost/**/bundles_current.test`: `TOTAL 500 PASS 499 FAIL 1 SKIP 0 XFAIL 0`, `BASELINE OK` (`0` new failures; the sole failure `conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax` is a pre-existing baseline entry).
- **Bundle & repository hygiene checks**:
  - All 36 `tests/selfhost/**/gen_*.py --check` and `tests/std/channel/gen_tests.py --check`: exit `0`, zero `DIFFERS`.
  - `python tools/archcheck.py`: `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T432`: clean (`0 REFUSED`, `0 UNLISTED`).
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` and `harness_check.py`: `OK` / `HARNESS OK`.

## Files changed
- _workspaces/baseline-failures.txt
- compiler/driver/pipeline.ax
- compiler/mir/async_lower.ax
- compiler/mir/builder.ax
- compiler/resolve/resolver.ax
- compiler/traits/mod.ax
- compiler/traits/solver.ax
- compiler/types/typeck.ax
- std/core/prelude.ax
- tests/run/trait2/test_derive.ax
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
- tests/selfhost/hir/qa_hir_corpus.ax
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax
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
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/std/channel/channel_big_struct.ax
- tests/std/channel/channel_boundary_edge.ax
- tests/std/channel/channel_bounded_basic.ax
- tests/std/channel/channel_move_only_drop.ax
- tests/std/channel/channel_mpmc_threads.ax
- tests/std/channel/channel_mpsc_threads.ax
- tests/std/channel/channel_spsc_threads.ax
- tests/std/channel/channel_unbounded_basic.ax
- tests/std/core/qa_generic_method.ax
- tests/typeck/async/async_basic_pos.thir
- tests/typeck/async/ordering_cmp_and_atomic_paths.ax

STATUS: COMPLETE round=0

# T495 Report — Fix regression: `impl<T> Drop` calling a generic inherent method fails native link (`AX_LINK_UNDEFINED_SYMBOL`)

## Summary
Fixed the P0 regression introduced by `T489` (`f0f98f33`) where `impl<T> Drop for S<T>` calling an inherent method of `impl<T> S<T>` (such as `AsyncSender<T>::drop` calling `mut_view(*self).close()` in `tests/std/async/executor/async_channel_pipeline.ax`) failed native linking with `AX_LINK_UNDEFINED_SYMBOL: undefined symbol 'close'`, and where `impl<T> Drop for S<T>` also suffered silent field-offset / `size_of<T>()` miscompiles whenever `S<T>` contained `T`-typed fields.

### Root cause
1. `T489` (`f0f98f33`) updated `mb_item_cache()` and `mb_count_generic_params_in_hir()` in `compiler/mir/builder.ax` so inherent methods inside generic `impl<T> S<T>` blocks report `> 0` generic parameters and are emitted only as monomorphized clones (`close_I<n>E`), never as an unspecialized symbol `'close'`.
2. However, `mb_count_generic_params_in_hir()` explicitly exempted `impl<T> Drop for S<T>` via `mb_impl_is_lang_drop(...)`, returning `0`. As a result:
   - `mb_prepare_mono()` seeded `AsyncSender<T>::drop` (and every other generic `Drop` impl) unconditionally as an unspecialized function with `T = TY_PARAM(0)`.
   - Inside that unspecialized `drop` body, `mb_scan_or_rewrite_calls()` saw `T = TY_PARAM(0)` (not concrete), could not monomorphize `close`, and left a native call to the non-existent unspecialized symbol `'close'` (`AX_LINK_UNDEFINED_SYMBOL`).
   - Worse, any `impl<T> Drop for S<T>` on a struct with `T`-typed fields (e.g. `struct WithPayload<T> { before: i32, payload: T, after: i32 }`) ran with placeholder `TY_PARAM(0)` layout and `size_of<T>() == 8`, silently reading/mutating wrong field offsets even in `[interp]`.

### Fix (`compiler/mir/builder.ax`)
- **Removed the `mb_impl_is_lang_drop` exemption** from `mb_count_generic_params_in_hir()` (extracted `mb_find_enclosing_generic_impl()` and removed the now-dead `mb_impl_is_lang_drop` helpers), so `impl<T...> Drop for S<...>` is treated as a generic template with its impl's generic parameter count, just like other generic impls.
- **Monomorphize generic `Drop` impls on concrete dropped types during `mb_prepare_mono` / `mb_scan_or_rewrite_calls`**:
  - Added `mb_instantiate_drop_for_ty()` and `mb_enqueue_drop_insts_for_ty()` (with cycle-safe visited tracking and `mir_type_needs_drop_in` fast-path filtering) called for every `MIR_TERM_DROP` terminator (recursively traversing `TY_STRUCT`, `TY_TUPLE`, `TY_ENUM`, `TY_ARRAY`, `TY_CLOSURE`, and `TY_COROUTINE` fields) and every `TY_BUILTIN_DROP_IN_PLACE` call.
  - Generic arguments are deduced from the `drop` item's `self` parameter type, the enclosing `HIR_ITEM_IMPL`'s `item_type` (covering `self: mut_view<Self>` and `self: mut_view<Box>`), and `(*t).args` fallback.
  - When concrete arguments are found, `mb_mono_find_or_create()` creates the concrete clone (`drop_I<n>E`) and records `((ty.v << 1) | 1) -> (*inst).new_item` in `thir.expr_methods`, which `drop_find_impl_fn_with_thir()` in `compiler/mir/drop.ax` already queries first (requiring zero changes to `compiler/mir/drop.ax` or `compiler/traits/mono.ax`, keeping all minimal selfhost bundles clean).
  - For legacy unparameterized struct values (`arg_count == 0`, e.g., `box_new<T>() -> Box` in `tests/std/alloc/qa_box.ax`), falls back to seeding the unspecialized `drop` instance on demand (`mir_build_fn` checks `gcnt > 0 && inst == 0`, and `mb_dedup_mono_names` preserves distinct names when both an `ac == 0` instance and an `ac > 0` clone exist for the same `orig_item`).
- **Monomorphized `drop_in_place<S<ConcreteArgs>>(ptr)` lowering**:
  - Added `mb_rewrite_drop_in_place_call()` in `mb_scan_or_rewrite_calls()` (when `arena != 0`) so `drop_in_place` on a concrete struct with a monomorphized generic `Drop` impl lowers to `_p = ptr; _r = &mut (*_p); call drop_clone(move _r)`, dispatching directly to the concrete destructor in both `[interp]` and native LIR without emitting an undefined unspecialized `drop` reference.

## Files changed
- compiler/mir/builder.ax
- tests/run/generic_drop_inherent_method/drop_calls_close_no_t_field.ax
- tests/run/generic_drop_inherent_method/drop_calls_helper_with_t_field.ax
- tests/run/generic_drop_inherent_method/drop_in_place_generic_method.ax
- _workspaces/reports/T495-report.md

## Tests
All builds and test runs were performed inside `build-snap-T495` (HEAD `54bb796f` + T495 changes only, 36 selfhost bundle generators / 60 files regenerated cleanly):

1. **Unpatched HEAD failure verification** (`_workspaces/artifacts/compiler-cache/axiomc2_O1_f73b66829b77384d.exe`, `--no-cache -j 2 --filter generic_drop_inherent_method --verbose`):
   - `TOTAL 9 PASS 1 FAIL 8` (`WEAK-NATIVE 0`):
     - `drop_calls_close_no_t_field.ax`: `[interp]` PASS, `[native]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: close`), `[native-O1]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: close`).
     - `drop_calls_helper_with_t_field.ax`: `[interp]` FAIL (wrong field offsets: `drop:88:5:30` instead of `drop:30:35:300`), `[native]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: helper`), `[native-O1]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: helper`).
     - `drop_in_place_generic_method.ax`: `[interp]` FAIL (wrong field offsets + `size_of<T>() == 8`: `finish:2:8\nafter:71:82`), `[native]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: finish`), `[native-O1]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: finish`).

2. **Fresh Stage 1–3 Bootstrap & Fixed-Point** (`build-snap-T495`):
   - `python tools/build_axiomc.py --out build --stage 3`
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d (8535040 bytes)`
   - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`

3. **Targeted regression & compatibility verification (`build-snap-T495/build/axiomc2.exe`, `--no-cache -j 2`)**:
   - `async_channel_pipeline`: `TOTAL 3 PASS 3 FAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
   - `generic_inherent_field` (`T489` suite): `TOTAL 18 PASS 18 FAIL 0` (`WEAK-NATIVE 0`).
   - `generic_drop_inherent_method` (`T495` suite): `TOTAL 9 PASS 9 FAIL 0` (`WEAK-NATIVE 0`).
   - Legacy & nested generic `Drop` edge cases (`qa_box`, `qa_vec`, `qa_vec_box`, `escape_barriers_and_retention`, `box_closure_buffer_promotion`, `generic_drop_instances`, `qa_drop_count_generic`, `generic_pointer_drop`): `TOTAL 24 PASS 24 FAIL 0` (`WEAK-NATIVE 0`).
   - Full `std/async`, `std/channel`, `std/sync`, `std/thread` sweep (`-j 2`): `TOTAL 165 PASS 165 FAIL 0` (`WEAK-NATIVE 0`).

4. **Full Task Gate** (`build-snap-T495`):
   - `python tools/taskgate.py --task T495 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
   - `TASKGATE T495 exit=0`
   - `axtest: TOTAL 354 PASS 352 FAIL 0 SKIP 2 XFAIL 0` (own 3 ids / 9 PASS; affected 160 ids incl. all 31 selfhost bundles / 305 PASS, 2 SKIP; smoke 30 ids / 49 PASS; 0 failures)
   - `Baseline: BASELINE OK`, `Failing ids: none`
   - `WEAK-NATIVE: 0 in the task's own/changed tests`
   - `archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations`

5. **Change-set hygiene**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T495`: exit `0`, `0 REFUSED`, `0 UNLISTED`.

## Spec deviations
none

STATUS: COMPLETE round=0

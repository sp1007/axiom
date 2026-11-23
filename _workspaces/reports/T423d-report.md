# T423d Report — Fix: method-level bound naming an impl-level generic (`impl<R> W<R> { fn mk<F: FnOnce<R>>(f: F) }`)

## Summary
Resolved `T423d` (ADR-0046 D1; T423 report F3 / QA F4): method-level generic bounds (both inline `<F: FnOnce<R>>` and `where F: FnOnce<R>`) that reference generic parameters of an enclosing `impl` or `trait` now resolve, infer, type-check, and monomorphize across all passes. `std/fiber/mod.ax` restores `Fiber.new<F: FnOnce<R>>` and `Fiber.spawn<F: FnOnce<R>>` (SPEC-34 AXS-EXEC-053.3), the 3 fiber bundle suites (`tests/std/fiber`, `tests/conformance/p11/e11_5_executors`, `tests/perf/p11_executor`) are regenerated (`--check` green), and `tests/std/fiber/impl_generic_in_method_bound_xfail.ax` passes without `xfail` in `interp`, `native`, and `native-O1`.

### Root cause
`compiler/resolve/resolver.ax` (`resolve_single_item_body`) already pushes the `impl`/`trait` generic rib as the parent of each method's `fn_scope`, and leaves type arguments inside `AstGenericArgs` (`<...>`) unbound so `.resolved` dumps preserve `(PathSegment "T")` parity with `axiom0`. Lowered `HirGenericArgs` are instead resolved in `compiler/types/typeck.ax`, where four defects prevented method bounds from seeing or substituting enclosing `impl`/`trait` generics:
1. **Missing enclosing `impl`/`trait` scope and corrupted symbol map when evaluating call-site bounds (`tc_callable_bound_to_subst_fn_ty`, `check_future_bound_outputs_for_call`).** At method call sites, `tc_callable_bound_to_subst_fn_ty` switched `cx.current_fn` to `fn_def` without setting `cx.current_impl` to `fn_def`'s enclosing `impl`/`trait` (leaving `cx.current_impl` null or pointing at the caller's `impl`), so `hir_type_to_typeid` could not find `R` inside `FnOnce<R>` and emitted `AX_NAME_UNRESOLVED`. In addition, calling `build_item_generic_param_args(cx, fn_def)` overwrote `thir.symbol_types` for `fn_def`'s generic parameter symbols with 0-based indices instead of `impl_n + idx`.
2. **Method-only substitution slice passed to bound helpers (`check_expr_method_call`, `tc_build_callable_hint_ty`, `check_callable_bound_outputs_for_call`, `check_future_bound_outputs_for_call`).** `expr_substs[expr]` stores only the method's own `own_n` type arguments (as required by `mir/builder.ax`), whereas `TY_PARAM` indices inside an `impl`/`trait` method's signature and bounds are numbered `[0..impl_n)` for the enclosing `impl`/`trait` and `[impl_n..impl_n + own_n)` for the method. Passing `method_substs` instead of the combined `[impl_args..., method_args...]` slice (`bound_substs`) left `impl` parameters unsubstituted or mis-indexed.
3. **Calling a generic callable parameter inside a generic `impl` method (`check_call_rest` `TY_PARAM` branch, `tc_find_callable_bound_in_item`).** `TY_PARAM.param_index` on a method parameter includes the `impl_n` prefix, so passing raw `p_idx` to `tc_find_callable_bound_in_item` mis-indexed `cx.current_fn`'s generic parameter list and did not check `cx.current_impl` when calling an `impl`-level callable parameter.
4. **Unchecked bound type arguments on uncalled items and generic user trait bounds (`register_item_sig`, `tc_check_generic_trait_bounds_for_call`).** Type arguments inside `<...>` of bounds were only resolved when callable/Future call-site helpers ran, so unknown names in uncalled method bounds went undiagnosed while called ones could diagnose per call site; furthermore, non-callable/non-Future generic trait bounds (`U: IntoVal<T>`) only checked trait name/self-type in `solver.ax` without unifying `<T>`, and `check_callable_bound_outputs_for_call` ignored closure parameter arity/type mismatches.

### Fix (`compiler/types/typeck.ax` & `std/fiber/mod.ax`)
- Added `tc_fn_enclosing_impl` (covering both `HIR_ITEM_IMPL` and `HIR_ITEM_TRAIT` members and their top-level shallow clones) and `tc_enter_callee_bound_scope`, saving and restoring `(current_fn, current_impl, self_ty)` cleanly without mutating `thir.symbol_types`.
- Added `tc_bound_arg_typeid` + `tc_check_item_bound_types` in `register_item_sig` / Pass 1b to resolve and cache every bound's `HirGenericArg.ty` in its declaring `(fn, impl/trait)` scope once, reporting `AX_NAME_UNRESOLVED` at the exact span even when uncalled and never duplicating diagnostics across call sites.
- Added `tc_build_method_call_comb_substs` (fast-pathing identity `Self<P0, ..>` receivers and unifying substituted `impl_self_ty` or `TY_PARAM` trait bounds for reordered/view `impl` headers) and threaded `bound_substs` (`[impl_args..., method_args...]`) into `tc_build_callable_hint_ty`, `check_future_bound_outputs_for_call` (enabling `Future<Output = R>` bounds on generic `impl` methods too), `check_callable_bound_outputs_for_call` (also enforcing closure parameter count and parameter type coercion), `tc_check_generic_trait_bounds_for_call` (verifying generic trait arguments such as `U: IntoVal<T>`), and post-call deep type-variable resolution on `ret_v` / `base_ty` without disturbing caller `TY_PARAM`s.
- Updated `check_call_rest` (`TY_PARAM`) and `check_expr_method_call` (`TY_PARAM` trait dispatch) to offset `p_idx` by `impl_n` and substitute trait generic arguments from bounds (`u.into_val()`).
- Restored `pub fn new<F: FnOnce<R>>(f: F) -> Fiber<Y, R>` and `pub fn spawn<F: FnOnce<R>>(f: F) -> Fiber<Y, R>` in `std/fiber/mod.ax`, regenerated the 3 fiber bundle suites, and removed `xfail` from `tests/std/fiber/impl_generic_in_method_bound_xfail.ax`.

## Files changed
- compiler/types/typeck.ax
- std/fiber/mod.ax
- tests/conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax
- tests/conformance/p11/e11_5_executors/fiber_switch_conformance.ax
- tests/perf/p11_executor/fiber_switch_overhead.ax
- tests/run/impl_generic_in_method_bound/caller_impl_assoc_and_self_params.ax
- tests/run/impl_generic_in_method_bound/inferred_and_explicit_type_args.ax
- tests/run/impl_generic_in_method_bound/inline_and_where_bound.ax
- tests/run/impl_generic_in_method_bound/trait_impl_method_bound.ax
- tests/run/impl_generic_in_method_bound/two_and_nested_impl_generics.ax
- tests/std/fiber/fiber_affinity.ax
- tests/std/fiber/fiber_deep_stack.ax
- tests/std/fiber/fiber_drop_cleanup.ax
- tests/std/fiber/fiber_host_contract.ax
- tests/std/fiber/fiber_nested.ax
- tests/std/fiber/fiber_panic_contained.ax
- tests/std/fiber/fiber_ping_pong.ax
- tests/std/fiber/fiber_scheduler_rr.ax
- tests/std/fiber/fiber_stack_sizes.ax
- tests/std/fiber/impl_generic_in_method_bound_xfail.ax
- tests/std/fiber/native_panic/np_after_yields.ax
- tests/std/fiber/native_panic/np_host_contract.ax
- tests/std/fiber/native_panic/np_main_thread.ax
- tests/std/fiber/native_panic/np_nested.ax
- tests/std/fiber/native_panic/np_resume_after_panic.ax
- tests/std/fiber/native_panic/np_scheduler.ax
- tests/std/fiber/native_panic/np_spawned_thread.ax
- tests/std/fiber/native_panic/qa_np_drop_not_run.ax
- tests/std/fiber/native_panic/qa_np_exit_passthrough.ax
- tests/std/fiber/native_panic/qa_np_plain_after.ax
- tests/std/fiber/native_panic/qa_np_thread_first.ax
- tests/std/fiber/native_panic/qa_np_three_deep.ax
- tests/std/fiber/qa_fiber_drop.ax
- tests/std/fiber/qa_fiber_foreign_collision.ax
- tests/std/fiber/qa_fiber_handle_reuse.ax
- tests/std/fiber/qa_fiber_many.ax
- tests/std/fiber/qa_fiber_nested3.ax
- tests/std/fiber/qa_fiber_resume_finished.ax
- tests/std/fiber/qa_fiber_values.ax
- tests/std/fiber/qa_fiber_yield_outside.ax
- tests/ui/impl_generic_in_method_bound/closure_result_mismatch.ax
- tests/ui/impl_generic_in_method_bound/unknown_name_in_method_bound.ax
- _workspaces/reports/T423d-report.md

## Verification
All builds and test runs executed inside isolated snapshot `build-snap-T423d/` (HEAD `8b6039f1` + `T423d` changes + snapshot-regenerated selfhost bundles):
1. **Stage-2/3 fixed-point bootstrap (`python tools/build_axiomc.py --out build --root . --stage 2`):**
   - `STAGE1 OK` (`axiomc1.exe`), `SEED-A (O1) OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 164020a33c504235e5c1265d7cb6062a7176cd4f62a8c629c75400a4807ce431` (9,372,160 bytes)
   - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`
2. **Before/after repro & new tests (`--no-cache -j 2`):**
   - Unpatched HEAD seed (`_workspaces/artifacts/compiler-cache/axiomc2_O1_508b6b133359e34a.exe`): `TOTAL 15 PASS 0 FAIL 15` (`AX_NAME_UNRESOLVED` on `std/fiber/impl_generic_in_method_bound_xfail.ax` and all 4 `run/impl_generic_in_method_bound/*.ax` across `interp`, `native`, `native-O1`).
   - Patched `build/axiomc2.exe`: `TOTAL 17 PASS 17 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (`std/fiber/impl_generic_in_method_bound_xfail.ax` 3/3, `run/impl_generic_in_method_bound/*` 12/12, `ui/impl_generic_in_method_bound/*` 2/2).
3. **Mutation liveness spot-proof (`build-snap-T423d/` only):**
   - Mutated expected `stdout:` on `run/impl_generic_in_method_bound/inline_and_where_bound.ax` (`32` -> `999`) -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all caught the byte mismatch), then restored -> `TOTAL 3 PASS 3 FAIL 0`.
4. **Bundle freshness & fiber suites (`--no-cache -j 2`):**
   - `tests/std/fiber/gen_tests.py --check`, `tests/conformance/p11/e11_5_executors/gen_tests.py --check`, `tests/perf/p11_executor/gen_tests.py --check`: all `OK`.
   - `std/fiber/`, `conformance/p11/e11_5_executors/`, `perf/p11_executor/`, `impl_generic_in_method_bound`: `TOTAL 149 PASS 146 FAIL 0 SKIP 0 XFAIL 3`, `WEAK-NATIVE 0`.
5. **Per-task gate (`python tools/taskgate.py --task T423d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):**
   - `TASKGATE T423d exit=0`: `TOTAL 707 PASS 702 FAIL 0 SKIP 5 XFAIL 0` (315 ids: `own` 17/17, `affected` 651/656 incl. `selfhost/{traits,typeck,typeck_traits,mir,opt,own_mir_verify,verify,backend,driver}`, `smoke` 53/53)
   - `WEAK-NATIVE: 0` in the task's own/changed tests
   - `BASELINE OK`, failing ids: none
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
   - `smoke-check (tests/smoke.list): OK`
6. **Full `tests/ui/`, `tests/run/`, and `selfhost/{resolve,resolve_hir,hir}` sweep (`-j 2`):**
   - `TOTAL 3704 PASS 3704 FAIL 0 SKIP 0 XFAIL 0`
7. **Task hygiene (`taskctl.py changes T423d` & `harness_check.py`):**
   - 0 `REFUSED`, `HARNESS OK`.

## Spec deviations
none

## Round 1

### QA Finding Addressed (F1)
- **Root cause:** In `compiler/types/typeck.ax` (`check_expr_method_call`), all four method-signature substitution branches (`comb_ptr` for generic methods on generic `impl`/`trait`, `trait_gslice` for non-generic methods on `TY_PARAM` trait receivers, `impl_gslice` for non-generic `impl` methods, and `fut_gslice` for `Future.poll`) called `subst_ty_self(..., slice, self_v)` — which substitutes **both** `MONO_SELF_PARAM_INDEX` (`Self`) and `TY_PARAM`s `[0..slice.count)` — and then immediately called `subst_ty_with_vars(..., slice)` on the already-substituted type. When the caller itself was inside a generic `impl` or `fn`, any caller `TY_PARAM` introduced from `slice` or `self_v` whose `param_index < slice.count` was re-substituted a second time through the callee's `slice` (and generic methods also fell through into the trailing `subst_ty_self(..., no_args, base_ty.v)` `else` branch). In addition, non-generic `impl` methods used raw receiver args `(*t).args` instead of `tc_build_method_call_comb_substs`, and `Self` (`TC_SELF_PARAM_INDEX`) inside `trait` method bounds was not substituted with the receiver `base_ty.v`.
- **Fix (`compiler/types/typeck.ax`):**
  - Added `tc_type_has_self_param`, `tc_deep_resolve_vars`, and `tc_subst_ty_and_self`: substitutes callee `TY_PARAM`s `[0..args.count)` **first** via `subst_ty_with_vars` (leaving `TC_SELF_PARAM_INDEX` / `MONO_SELF_PARAM_INDEX` `0xFFFFFF00` untouched), **then** replaces `Self` via `subst_ty_self(..., empty_args, self_v)` only when `ty` mentions `TC_SELF_PARAM_INDEX` (with a simultaneous single-pass `subst_ty_self` fallback if both `ty` and `args` mention `TC_SELF_PARAM_INDEX`), and finally resolves bound `TY_VAR`s deeply via `tc_deep_resolve_vars` (`vars_only = [0u32]`, which never substitutes any `TY_PARAM`).
  - Updated all `check_expr_method_call` signature substitution branches (`comb_ptr`, `gslice`, `trait_gslice`, non-generic `HIR_ITEM_IMPL` via `tc_build_method_call_comb_substs`, `impl_gslice`, `fut_gslice`, and `no_args`) to use `tc_subst_ty_and_self` once and gated the non-generic `if/else` chain on `!fn_sig_subbed`.
  - Threaded `callee_self_v` (`base_ty.v` on method calls, `0u32` on free calls) into `tc_build_callable_hint_ty`, `tc_callable_bound_to_subst_fn_ty`, `check_callable_bound_outputs_for_call`, `check_future_bound_outputs_for_call`, and `tc_check_generic_trait_bounds_for_call` / `tc_check_single_generic_trait_bound` via `tc_subst_ty_and_self`, and resolved `method_substs` entries via `tc_deep_resolve_vars`.
  - Added `tests/run/impl_generic_in_method_bound/caller_impl_assoc_and_self_params.ax` covering F1 Example 2 (`W<Y>.mk(|| -> Y { ... })`, `W.mk(...)`, and `W<X>.mk(...)` inside `impl<X, Y> Caller<X, Y>`), `Self` containing caller `TY_PARAM`s (`W<Y>`, `Pair<X, Y>`, and `trait WithSelf<R>` `Self` on `U: WithSelf<Y>`), swapped caller `TY_PARAM` slices (`[Y, X]`) on non-generic `impl` and `trait` methods, and non-generic methods on reordered `impl<A, B> RevPair<B, A>`.

### Round 1 Verification (`build-snap-T423d/`, HEAD `2e50e70a`)
1. **Stage-2/3 fixed-point bootstrap (`python tools/build_axiomc.py --out build --root . --stage 2`):**
   - `STAGE1 OK` (`axiomc1.exe`, `sha256=19ceb4040eba9edb`), `SEED-A (O1) OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == d5af7ab9c409fc479546a3c5bd373778f13de57e8a46b0a9fcfb6c74b8a63b68` (8,381,952 bytes)
   - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`
2. **QA repro + all `impl_generic_in_method_bound` tests (`--no-cache -j 2`):**
   - `TOTAL 24 PASS 24 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (incl. `qa_cross_impl_and_mixed_generics.ax` 3/3, `caller_impl_assoc_and_self_params.ax` 3/3, `qa_adversarial_bounds_reject.ax` 1/1, `std/fiber/impl_generic_in_method_bound_xfail.ax` 3/3).
3. **Mutation liveness spot-proof (`build-snap-T423d/` only):**
   - Mutated expected `stdout:` on `caller_impl_assoc_and_self_params.ax` (`62 50 169 88` -> `999 50 169 88`) -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all caught byte 0 mismatch), restored -> `TOTAL 3 PASS 3 FAIL 0`.
4. **Bundle generators (`--check`):**
   - `tests/std/fiber/gen_tests.py --check`, `tests/conformance/p11/e11_5_executors/gen_tests.py --check`, `tests/perf/p11_executor/gen_tests.py --check`: all `OK`.
5. **Per-task gate (`python tools/taskgate.py --task T423d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423d.json`):**
   - `TASKGATE T423d exit=0`: `TOTAL 723 PASS 715 FAIL 0 SKIP 5 XFAIL 3` (323 ids: `own` 57 ids / 153 PASS / 0 FAIL / 3 XFAIL, `affected` 288 ids / 658 PASS / 0 FAIL / 5 SKIP, `smoke` 33 ids / 56 PASS / 0 FAIL)
   - `WEAK-NATIVE: 0` in the task's own/changed tests
   - `BASELINE OK`, failing ids: none
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
   - `smoke-check (tests/smoke.list): OK`
6. **Task hygiene (`taskctl.py changes T423d` & `harness_check.py`):**
   - 0 `REFUSED`, `HARNESS OK`.

STATUS: COMPLETE round=1

# T446 Report — Fix: monomorphisation of impl-level generic parameters (FU-F, FU-G)

## Summary
Completed full monomorphisation of impl-level generic parameters for both inherent (`impl<F> T<F>`) and trait (`impl<F: Tr> Tr2 for T<F>`) impl blocks across typechecking, trait solving, mono seeding, and MIR construction (T422 FU-F, FU-G; ADR-0042 §2). Building on the inherent-impl and generic-`Drop` groundwork landed in `T489` (`f0f98f33`) and `T495` (`58b4e97d`), this task eliminates the remaining impl-generic monomorphisation bugs:

### Root causes & fixes
1. **Place projections ignored in MIR mono call scanning (`compiler/mir/builder.ax`):**
   - `mb_scan_or_rewrite_calls` read `(*mir_local_at((*body).locals, local)).ty` instead of `mir_drop_place_type(view(*body), view(*thir), view(place))` for:
     - Trait-method receiver lookup (`a0`): calling a by-value trait method on a field (`self.f.consume()`) or a trait method on a `mut_view<F>` field (`self.fut.poll(arg)`) saw the enclosing struct type (`Wrap<F>`) instead of `F`, causing infinite recursion / stack overflow (`0xC00000FD`) or crash (`0xC0000005`).
     - Generic argument and destination deduction (`arg_op`, `destination`): passing a projected field by value to a generic free function (`show_val(self.fut)`, `show_pair(self.flag, self.fut)`) deduced `T = Wrap<F>` instead of `T = F` / `u32`, silently miscompiling `size_of<T>()` and layout.
   - `mb_coroutine_receiver_ty` likewise rejected `proj_count != 0`; updated to use `mir_drop_place_type`.

2. **Trait identity ignored during MIR trait-method dispatch (`compiler/mir/builder.ax`):**
   - `mb_scan_or_rewrite_calls` matched any `HIR_ITEM_IMPL` with a `trait_path` whose receiver matched and had a member with the same method name, without verifying that `(*iit).trait_path` implements the trait owning `trait_method`. When a type implemented two traits with the same method name (e.g. `Tr1.val` and `Tr2.val`), `self.b.val()` under `B: Tr2` dispatched to `Tr1.val` (the first impl in scope).
   - Stored the owning `HIR_ITEM_TRAIT` in `mb_item_cache` at `(m as usize) | 3`, added `mb_owner_trait_of_member`, and added two-pass trait-matched lookup in `mb_scan_or_rewrite_calls` (exact trait match first, supertrait/untyped fallback second).

3. **Explicit generic calls & associated functions without `self` on generic impls (`compiler/mir/builder.ax`):**
   - `show<F>()` called inside `impl<F> Wrap<F>` or `impl<F: Future<Output = i64>> Future for W<F>` and associated functions without `self` (`Wrap<S16>.f_size()`) could not be deduced from value arguments/return type after HIR lowering, leaving placeholder `size_of<F>() == 8` in `[interp]` and `AX_LINK_UNDEFINED_SYMBOL: show` / `f_size` in `[native]`/`[native-O1]`.
   - In `mb_build_control_or_call_expr`, when `thir_is_mono_prepared` is active:
     - `HIR_EXPR_CALL` resolves `(*thir).expr_substs[callee_expr]` through `mb_resolve_ty` (substituting the caller's `b.subst_args` and `b.self_ty_v`) and instantiates concrete callees directly via `mb_mono_find_or_create` (enqueuing them into the worklist for transitive instantiation).
     - `HIR_EXPR_METHOD_CALL` for non-trait generic methods deduces impl-level arguments from the receiver type (`impl_it` item type + `(*base_t).args`) and combines them with resolved method-level `expr_substs[expr]` args to instantiate directly via `mb_mono_find_or_create`.

4. **Default trait methods inherited by generic trait impls (`compiler/mir/builder.ax`):**
   - `mb_instantiate_default` substituted `Self` with the impl's unspecialized `self_type` (`W<TY_PARAM(0)>`) using `no_args` instead of substituting `b.subst_args` into `self_v` and passing `b.subst_args` to `subst_ty_self`. Inside `W<B>::doubled()`, `self.base()` remained unspecialized and linked against `A::base` natively (`26 20` instead of `54 218`) and called `A::doubled` in `[interp]` (`54 42`).
   - Added `self_ty_v: u32` to `MirBuilder`, resolved it in `mir_build_fn_subst` from `(func | 2)` substituted by `b.subst_args`, threaded `b.self_ty_v` into `mb_resolve_ty` (so `size_of<Self>()` and `needs_drop<Self>()` inside default methods also see the concrete `Self`), and updated `mb_instantiate_default` to substitute with `b.subst_args` and use `mir_drop_place_type`.

5. **Simultaneous impl-level and method-level generics (`compiler/types/typeck.ax`, `compiler/traits/solver.ax`, `compiler/mir/builder.ax`):**
   - Both `current_impl` and `current_fn` generic parameters started at index `0`, colliding on `TY_PARAM(0)` (`AX_VERIFY_CALL_SIGNATURE` on `impl<F> Wrap<F> { fn combine<U>(...) }`).
   - Assigned impl params `0 .. impl_n - 1` and method params `impl_n .. impl_n + own_n - 1` across `typeck.ax` (`tc_resolve_generic_param_sym`, `lookup_path_type`, `HIR_EXPR_METHOD_CALL` combined substitution, `resolve_future_output_ty`), `solver.ax` (`ty_param_allows_trait`, `param_satisfies_auto_trait`, also resolving scope-local generic param names via `solver_item_param_name_sv` so method-level `where F: Tr` clauses match regardless of `TY_PARAM(0)`'s interned name), and `mir/builder.ax` (`mb_count_generic_params_in_hir` returns `impl_n + own_n`).

6. **Generic impl seeding hygiene (`compiler/traits/mono.ax`):**
   - `mono_seed_hir_items` now skips `HIR_ITEM_IMPL` items with generic parameters via `impl_has_generic_params` so unspecialized impl methods and default methods are never seeded with empty type arguments.

## Files changed
- compiler/traits/mono.ax
- compiler/traits/solver.ax
- compiler/types/typeck.ax
- compiler/mir/builder.ax
- tests/run/generic_impl_mono/fuf_layout_size_needs_drop.ax
- tests/run/generic_impl_mono/fug_trait_dispatch_and_free_call.ax
- tests/run/generic_impl_mono/trait_disambiguation_and_projections.ax
- tests/run/generic_impl_mono/default_method_and_method_generics.ax
- _workspaces/reports/T446-report.md

## Tests
All builds and test runs were performed inside `build-snap-T446/` (HEAD `c92e92ca` + T446 changes only; 36 selfhost bundle generators / 60 files regenerated cleanly):

1. **Unpatched HEAD failure verification** (`_workspaces/artifacts/compiler-cache/axiomc2_O1_adb3dbb652075521.exe`, `--no-cache -j 2 --filter run/generic_impl_mono --verbose`):
   - `TOTAL 12 PASS 0 FAIL 12` (`WEAK-NATIVE 0`):
     - `fuf_layout_size_needs_drop.ax`: `[interp]` FAIL (`8 8` instead of `16 24`), `[native]`/`[native-O1]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: f_size`).
     - `fug_trait_dispatch_and_free_call.ax`: `[interp]` FAIL (exit `1`, expected `77`), `[native]`/`[native-O1]` FAIL (`AX_LINK_UNDEFINED_SYMBOL: show`).
     - `trait_disambiguation_and_projections.ax`: `[interp]` TIMEOUT (infinite recursion), `[native]`/`[native-O1]` CRASH (`3221225725` / `0xC00000FD`).
     - `default_method_and_method_generics.ax`: `[interp]`/`[native]`/`[native-O1]` FAIL (`AX_VERIFY_CALL_SIGNATURE`).

2. **Stage 1–3 Bootstrap & Fixed-Point** (`build-snap-T446`):
   - `python tools/build_axiomc.py --out build --stage 3`
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 1ff738f4a890f7fadb24137c48a398ac744ddff998c163ab26a8206d6473fe85 (8559104 bytes)`
   - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`

3. **Own regression tests (`build-snap-T446/build/axiomc2.exe`, `--no-cache -j 2 --filter run/generic_impl_mono --verbose`)**:
   - `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 4 tests pass in `interp`, `native`, and `native-O1` with exact `// stdout:` and non-zero `// exit:`).

4. **Required suites (`tests/run/generic*`, `tests/run/trait*`, `tests/std`, `-j 2`)**:
   - `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 2 --filter run/generic --filter run/trait --filter std/`
   - `TOTAL 382 PASS 382 FAIL 0 SKIP 0 XFAIL 0`.

5. **Full Task Gate (`build-snap-T446`)**:
   - `python tools/taskgate.py --task T446 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
   - `TASKGATE T446 exit=0`
   - `axtest: TOTAL 468 PASS 466 FAIL 0 SKIP 2 XFAIL 0` (own 4 ids / 12 PASS; affected 228 ids incl. selfhost bundles / 419 PASS, 2 SKIP; smoke 30 ids / 51 PASS; 0 failures)
   - `Baseline: BASELINE OK`, `Failing ids: none`
   - `WEAK-NATIVE: 0 in the task's own/changed tests`
   - `archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations`

6. **Change-set hygiene**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T446`: exit `0`, 0 REFUSED.

## Spec deviations
none

## Status
STATUS: COMPLETE round=0

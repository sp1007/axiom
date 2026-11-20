# T489 report

## Summary
Fixed the silent miscompile (T485 gate follow-up F-2, REQ-OPT-292) where methods of generic inherent `impl` blocks reading fields of a struct containing a `T`-typed field returned wrong values (`0` instead of `3` for `view<Wrap<T>>`, and `0`/`1` in interp/native for by-value `self`).

### Root cause
1. `mb_item_cache` (`compiler/mir/builder.ax:1752`) and the uncached fallback loop in `mb_count_generic_params_in_hir` (`compiler/mir/builder.ax:11129`) gated enclosing-impl generic lookup on `(unsafe { (*it).trait_path as usize }) != 0`. Consequently, methods of generic **inherent** impls (`impl<T> Wrap<T>`, where `trait_path == null`) returned `0` generic parameters.
2. Because `mb_count_generic_params_in_hir` returned `0`, `mb_prepare_mono` seeded the unspecialized inherent method as a non-generic function and `mb_scan_or_rewrite_calls` never deduced `T` or instantiated a monomorphized clone. Inside the unspecialized body, `Wrap<T>` still contained `TY_PARAM(0)` (8-byte placeholder alignment in `layout.ax`), which reordered `v: T` ahead of `k: i32` (4-byte alignment) to offset 0 and pushed `k` to offset 8, causing `self.k` to read out of bounds on a concrete `Wrap<i32>` (where `k` is at offset 0 and `v` at offset 4).
3. Two related issues uncovered during root-cause analysis and gating were fixed in the same file (`compiler/mir/builder.ax`):
   - **Cross-instantiation method calls (`HIR_EXPR_METHOD_CALL`, lines 8818–8920):** When lowering a call to a generic method (own generic params or generic impl member), `mb_item_ty` substituted the *caller's* `b.subst_args` into the callee's generic parameters and typed the auto-ref `view`/`mut_view` temp from that substituted signature instead of `intern_view_ty(recv_ty, is_mut_ref)`. When a generic body instantiated at `i32` called a generic inherent method on `Wrap<Wide>`, `callee_op.constant.ty` and the auto-ref temp leaked `i32` into argument deduction. Generic method calls now keep the callee's raw item type for deduction and type auto-ref temps from `recv_ty`.
   - **Strict interpreter UB in `mb_item_cache` (`AX_UNSAFE_INTERP_UB`):** Once `mb_item_cache` indexed generic inherent impls (such as `impl<T> Poll<T>` in `std.core.prelude`), `qa_obj_link_driver_smoke.ax [interp]` hit `mb_item_cache`'s pre-existing `n as *const HirItem` integer-to-pointer cast under `| 4` (`usize as ptr: address not in a live allocation`). Removed the `| 4` integer-as-pointer map entries altogether; the rare tiebreaker when address-match (`pa`) and symbol-match (`pb`) point to two distinct generic impls now walks `(*cur).next` to determine list order with zero integer-to-pointer casts.

### Compiler-wide grep audit (trait-only / impl-generic checks)
Audited every `trait_path` and `generic_params` check across `compiler/`:
- `compiler/mir/builder.ax:1752` (`mb_item_cache`) — **fixed** (removed `trait_path != 0` guard).
- `compiler/mir/builder.ax:11129` (`mb_count_generic_params_in_hir` fallback) — **fixed** (removed `trait_path != 0` guard).
- All remaining `trait_path != 0` checks in `compiler/mir/builder.ax` (`:10535` `mb_impl_member_for`, `:11059` `mb_impl_is_lang_drop`, `:11411` `mb_coroutine_method`, `:11627` trait-method dispatch in `mb_scan_or_rewrite_calls`), `compiler/mir/async_lower.ax:2213`, `compiler/mir/drop.ax:252,321`, `compiler/traits/solver.ax` (overlap, default methods, associated types, auto traits, bound satisfaction, `Send`/`Share` safety, supertraits), `compiler/traits/mono.ax:1132,1186`, `compiler/hir/lower.ax:1602,1653`, `compiler/own/unsafe.ax:884`, `compiler/resolve/resolver.ax:909,936`, and `compiler/types/typeck.ax` (lang `Drop`, default method instantiation) are genuinely trait-specific.
- Further sites that inspect only `(*fn_item).generic_params` without checking an enclosing `HIR_ITEM_IMPL.generic_params` (not trait-only, and safe or outside T489 paths; listed for follow-up):
  1. `compiler/traits/mono.ax:1176-1186` (`mono_seed_hir_items`): seeds `HIR_ITEM_IMPL` members via `item_is_non_generic_fn(m)` without checking `(*it).generic_params` (overwritten by `mb_prepare_mono` in the driver; only observable through `session_typeck_and_seed_mono`).
  2. `compiler/driver/pipeline.ax:5351-5360` (`pipe_item_has_own_generics`, used at `:5731`, `:5798`): checks only `(*it).generic_params`. Safe for emission because `pipe_build_item_body` calls `mir_build_fn(..., mono=0)` which uses `mb_count_generic_params_in_hir` and skips unspecialized impl-generic items, though `:5798` still adds std generic impl methods to `std_cands`.
  3. `compiler/driver/pipeline.ax:3631` (`pipe_any_hir_fn_uses_name`): checks only `(*it).generic_params` on top-level `HIR_ITEM_FN` (including shallow-cloned impl members) when checking exported-const symbol collisions.
  4. `compiler/backend/session.ax:2490` (`backend_resolve_body_call_types`): checks only `(*callee).generic_params` when refreshing `terminator.func.constant.ty`; safe after monomorphization because calls are rewritten to mono clones with concrete item types.
  5. `compiler/own/unsafe.ax:976-995` (`conc_type_satisfies_auto`): checks `(*c.current_fn).generic_params` / `where_clause` for `Send`/`Share` bounds on `TY_PARAM`, not enclosing `impl` generics.
  6. `compiler/traits/solver.ax:2630` (`check_call_bounds`): checks `(*callee_it).generic_params` / `where_clause`, not enclosing `impl` generics.
  7. `compiler/types/typeck.ax:4164-4196` (`lookup_path_type_by_name`): both `current_fn` and `current_impl` parameter indices start at `0` (method-level `<U>` inside `impl<T>` would collide on index 0; outside T489 paths).

## Files changed
- compiler/mir/builder.ax
- tests/run/generic_inherent_field/before_and_after_t_two_insts.ax
- tests/run/generic_inherent_field/by_value_self.ax
- tests/run/generic_inherent_field/method_calling_method.ax
- tests/run/generic_inherent_field/mut_view_self.ax
- tests/run/generic_inherent_field/view_self_repro.ax
- _workspaces/reports/T489-report.md

## Tests
All builds and test runs were performed inside `build-snap-T489` (HEAD `f4b64ad5` + T489 changes only, regenerated selfhost bundles):

1. **HEAD reproduction (before fix, `axiomc2.exe` sha256 `fb6e209d8d9c2405`):**
   - `struct Wrap<T> { k: i32, v: T }; impl<T> Wrap<T> { fn get(self: view<Wrap<T>>) -> i32 { self.k } }; fn main() -> i32 { let a = Wrap<i32> { k: 3, v: 1 }; a.get() }`
   - `run --interp`: exit `0` (expected `3`); `build` (O0): exit `0`; `build -O1`: exit `0`.
   - After fix (`axiomc2.exe` sha256 `99bdeab056842d15`): `run --interp`: exit `3`; `build` (O0): exit `3`; `build -O1`: exit `3`.

2. **Stage-2 / Stage-3 bootstrap and fixed point:**
   - `python tools/build_axiomc.py --out build --stage 3`
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 99bdeab056842d15b9b9d2aece282366a4e41f2ec3ed281411505c7e05e87c72 (8360960 bytes)`
   - `STAGE0-GUARD OK: axiomc1 and B produced byte-identical .exe on 6 smoke program(s) (O1, incl. Xin chào thế giới)`

3. **Own regression tests (`tests/run/generic_inherent_field/`):**
   - `python tools/axtest.py --compiler build/axiomc2.exe --no-cache --filter run/generic_inherent_field --verbose`
   - `TOTAL 15 PASS 15 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 5 tests pass in `interp`, `native`, and `native-O1`, each verifying both stdout and non-zero exit code).

4. **Mutation proof (in snapshot only, then restored):**
   - Changed `// exit: 6` -> `// exit: 5` in `build-snap-T489/tests/run/generic_inherent_field/view_self_repro.ax`:
     - `FAIL run/generic_inherent_field/view_self_repro.ax [interp]: exit code 6, expected 5`
     - `FAIL run/generic_inherent_field/view_self_repro.ax [native]: exit code 6, expected 5`
     - `FAIL run/generic_inherent_field/view_self_repro.ax [native-O1]: exit code 6, expected 5`
     - `TOTAL 3 PASS 0 FAIL 3` (exit 1).
   - Restored file and re-ran: `TOTAL 15 PASS 15 FAIL 0` (exit 0).

5. **Targeted std generic-inherent-impl sweep (`conformance/p11`, `run/async`, `run/concurrency`):**
   - `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 2 --filter conformance/p11 --filter run/async --filter run/concurrency`
   - `TOTAL 216 PASS 216 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

6. **Full task gate (`tools/taskgate.py`):**
   - `python tools/taskgate.py --task T489 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
   - `TASKGATE T489 exit=0`
   - `axtest: TOTAL 456 PASS 454 FAIL 0 SKIP 2 XFAIL 0` (own 5 ids / 15 PASS; affected 198 ids / 411 PASS, 2 SKIP; smoke 30 ids / 45 PASS; 0 failures)
   - `Baseline: BASELINE OK`, `Failing ids: none`, `WEAK-NATIVE: 0 in the task's own/changed tests`
   - `archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations`

## Spec deviations
none

## Follow-ups
- Consider auditing and unifying the remaining `(*fn).generic_params`-only checks listed in the audit above (`mono_seed_hir_items`, `pipe_item_has_own_generics`, `conc_type_satisfies_auto`, `check_call_bounds`, and simultaneous `impl<T> { fn m<U>(...) }` parameter indexing in `compiler/types/typeck.ax:4164-4196`).
- `std/async/timeout.ax:130` (`FU-F`) can now be re-evaluated alongside `FU-B`/`FU-C`/`FU-G` since `impl<F>` inherent methods are now monomorphized with concrete field layouts.

STATUS: COMPLETE round=0

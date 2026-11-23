# T422d report — Fix native `.await` on generic `Future` impl and generic `async fn`

## Summary

Fixed native `.await` resolution, monomorphization, coroutine state-machine lowering, and nested generic `Self`-type deduction for generic `Future` implementations (`impl<T> Future for Wrap<T>`, `impl<T> Future for Wrap<Wrap2<T>>`) and generic `async fn`s (`async fn f<T>(...)`). Added 4 three-mode (`interp`, `native`, `native-O1`, exact `stdout:`, `WEAK-NATIVE: 0`) regression tests in `tests/run/await_generic_future/` and removed all remaining `// native-after: T422d` markers (`spec34_task_group_example` and `spec34_local_executor_example` in `tests/std/async/structured/`).

## Root cause & changes

1. **Trait solver & nested generic `Self` structural matching (`compiler/traits/solver.ax`):**
   - Added `ImplBindState` + recursive `pattern_ty_matches_target` (handling nested `TY_STRUCT`, `TY_ENUM`, `TY_COROUTINE`, views/pointers, arrays/slices, tuples, fn types, and consistent `TY_PARAM` binding at `depth > 0`) and wired `type_matches_impl_self_exact`, `get_impl_deduced_generic_arg`, and `impl_bounds_satisfied` so nested generic impl headers such as `impl<T> Future for Wrap<Wrap2<T>>` match structurally without colliding with sibling impls (`Wrap<Alt<T>>`).
   - Updated `type_satisfies_auto_trait` and `find_auto_trait_failure_reason` on `TY_COROUTINE` to inspect `(*t).fields[1..field_count]` once lowered (`field_count > 0`) and guard pre-lowering `args` checks with `!coro_def_has_generics` so generic `TY_COROUTINE` type arguments remain preserved on `args`.

2. **Coroutine generic type parameters & `Future.Output` deduction (`compiler/types/typeck.ax`, `compiler/traits/mono.ax`):**
   - Populated `TY_COROUTINE` generic parameter `TypeId`s in `register_item_sig` (`compiler/types/typeck.ax`) so distinct instantiations (`gen_async<i64>` vs `gen_async<bool>`) intern to distinct `TY_COROUTINE` keys even when `Output` does not mention `T`, and re-indexed post-inference `TY_COROUTINE` entries in `finalize_types`.
   - Added recursive `tc_deduce_impl_args` in `resolve_future_output_ty` (`compiler/types/typeck.ax`) so `.await` on nested generic futures (`Wrap<Wrap2<i64>>`) deduces the `impl`'s own generic arguments (`[i64]`) against `imp_self_ty` before substituting `type Output` via `tc_subst_ty_and_self`.
   - Extended `type_contains_param`, `subst_ty_self`, and `deduce_args` in `compiler/traits/mono.ax` to handle `TY_COROUTINE` (`ret_type`, `args`, and lowered `fields`).

3. **Monomorphizing synthesized `Future.poll` calls & generic `async fn` clones (`compiler/mir/builder.ax`, `compiler/mir/async_lower.ax`, `compiler/own_mir_verify/session.ax`):**
   - Preserved `(*coro_mut).args` / `arg_count` in `mir_lower_async_body` (`compiler/mir/async_lower.ax`) and in `session_own_check_body` (`compiler/own_mir_verify/session.ax`, saving/restoring around `verify_mir_own`), and propagated lowered coroutine state layout across structurally equal post-inference `TY_COROUTINE` entries (`al_types_structurally_eq`).
   - Replaced ASLR-dependent pointer-XOR symbol synthesis in `mir_lower_async_body` with deterministic symbol allocation (`resolve_next_sym_v` / `MonoEngine.next_sym_id`) so stage-2/3 native builds remain deterministic (`FIXED-POINT (O1) OK`).
   - Added `mir_resolve_poll_callee_mono` (`compiler/mir/builder.ax`) + `async_resolve_poll_calls_mono` (`compiler/mir/async_lower.ax`) to match exact `Future` impls, deduce impl generic arguments from the awaited receiver type, instantiate concrete `MonoInstance`s, and rewrite synthesized `Future.poll` call terminators to the concrete monomorphized symbol and substituted `TY_FN`.
   - Preserved original method names in `mb_dedup_mono_names` (`mb_preserve_orig_item_name`) and updated prebuilt `MirBody.fn_name` on collision renames.
   - Orchestrated `session_lower_all_async` (`compiler/own_mir_verify/session.ax`) as a fixpoint loop: lower non-generic `async fn`s -> prepare `MonoEngine` -> iteratively lower concrete `MonoInstance` clones of generic `async fn`s (registering each synthesized `poll_it` in `MonoEngine` for `pipe_is_mono_clone` and scanning coroutine `Drop` glue + callees), resolve synthesized `Future.poll` calls, and drain `MonoEngine`'s worklist -> run `mir_finish_mono_for_async` (`mb_dedup_mono_names`). Uninstantiated generic `async fn` templates are MIR-verified and own-checked without lowering or drop-elaborating unmonomorphized `MIR_TERM_SUSPEND` terminators.

## Verification (isolated snapshot `build-snap-T422d/`, `-j 2`)

- **Stage-2/3 Fixed-Point & Stage-0 Guard (`python tools/build_axiomc.py --out build --root . --stage 2`):**
  - `STAGE1 OK`: `axiomc1.exe` (`32539648` bytes, `sha256=88d412ccf57308cf`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 221e7c1f40d2cdb0237765efbd9575998f83e0ba8012f4143a18339cefa9c3d5` (`8659456` bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and `axiomc2` produced byte-identical `.exe` on all 6 smoke programs.
- **3-Mode Own & Structured Async Tests (`python tools/axtest.py --compiler build/axiomc2.exe --filter run/await_generic_future --filter std/async/structured --no-cache -j 2 --verbose`):**
  - `TOTAL 62 PASS 62 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 4 `tests/run/await_generic_future/*.ax` tests plus all `tests/std/async/structured/*.ax` tests — including un-gated `spec34_task_group_example.ax` and `spec34_local_executor_example.ax` — passed in `interp`, `native`, and `native-O1`).
  - `git grep "native-after: T422d"` across `compiler`, `tests`, `std`, `spec`, `tools`: 0 matches.
  - `python tests/std/async/structured/gen_tests.py --check`: `OK structured bundles match live std/async`.
- **Native-Evidence Mutation Spot-Proof (inside `build-snap-T422d/` only):**
  - Mutated `seed + 2i64` -> `seed + 3i64` in `build-snap-T422d/tests/run/await_generic_future/repro_wrap_generic_future.ax`: `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed).
  - Restored byte-identical (`sha256=8f2022d91c1c4376...`) and re-ran: `TOTAL 3 PASS 3 FAIL 0`.
- **Per-Task Gate (`python tools/taskgate.py --task T422d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):**
  - `own`: 22 ids, 62 results, 62 PASS, 0 FAIL, 0 SKIP
  - `affected`: 254 ids, 481 results, 479 PASS, 0 FAIL, 2 SKIP
  - `smoke`: 33 ids, 56 results, 56 PASS, 0 FAIL, 0 SKIP
  - `total (dedup)`: `TOTAL 532 PASS 530 FAIL 0 SKIP 2 XFAIL 0`
  - `WEAK-NATIVE`: 0 in task's own/changed tests; `archcheck`: clean (232 files, 0 violations); `smoke-check`: OK; `TASKGATE T422d exit=0`.

## Files changed

- compiler/mir/async_lower.ax
- compiler/mir/builder.ax
- compiler/own_mir_verify/session.ax
- compiler/traits/mono.ax
- compiler/traits/solver.ax
- compiler/types/typeck.ax
- tests/run/await_generic_future/await_in_generic_async_fn.ax
- tests/run/await_generic_future/nested_generic_future.ax
- tests/run/await_generic_future/repro_wrap_generic_future.ax
- tests/run/await_generic_future/two_instances_wrap_i64_bool.ax
- tests/std/async/structured/gen_tests.py
- tests/std/async/structured/spec34_local_executor_example.ax
- tests/std/async/structured/spec34_task_group_example.ax

## Status

STATUS: COMPLETE round=0

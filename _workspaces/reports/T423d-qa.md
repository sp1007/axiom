# T423d QA Report — Impl-level generics in method bounds

## Round 0

### Summary
Reviewed `compiler/types/typeck.ax`, `std/fiber/mod.ax`, `tests/std/fiber/impl_generic_in_method_bound_xfail.ax`, and all 6 new tests in `tests/{run,ui}/impl_generic_in_method_bound/`. Verified bundle generators (`--check`), stage-2/3 fixed-point compiler (`sha256=164020a33c504235e5c1265d7cb6062a7176cd4f62a8c629c75400a4807ce431`), native-evidence mutation spot-proof, `taskgate.py`, `taskctl.py changes T423d`, and `harness_check.py`.

All engineer-added tests, `tests/std/fiber/impl_generic_in_method_bound_xfail.ax`, and the QA adversarial UI test (`qa_adversarial_bounds_reject.ax`) pass. However, QA boundary cross-checking uncovered **1 FAIL finding** in `check_expr_method_call`: calling a generic `impl` method whose bound/signature uses impl-level + method-level generics from inside another generic `impl` double-substitutes caller `TY_PARAM`s through `comb_ptr` (`subst_ty_self` followed by `subst_ty_with_vars` with the same `comb_ptr`).

### Findings

#### F1 (FAIL) — Double-substitution of caller `TY_PARAM`s in `check_expr_method_call` when calling a generic `impl`/`trait` method from inside another generic `impl`
- **Location:** `compiler/types/typeck.ax:9279-9280` (and the same pattern at `9303-9304` for trait `TY_PARAM` receivers and `9308-9309` for non-generic impl methods):
  ```axiom
  let self_sub = unsafe { subst_ty_self(mut_view((*cx.thir).interner), (TypeId { v: fn_ty_id.v }), view(*comb_ptr), base_ty.v) };
  let sub_fn = unsafe { subst_ty_with_vars(mut_view((*cx.thir).interner), mut_view(cx.type_vars), (TypeId { v: self_sub.v }), view(*comb_ptr)) };
  ```
- **Root cause:** `compiler/traits/mono.ax:242-275` (`subst_ty_self`) substitutes **both** `MONO_SELF_PARAM_INDEX` (`Self`) **and** every `TY_PARAM` indexed into `args` (`*comb_ptr` / `trait_gslice` / `impl_gslice`). Immediately calling `subst_ty_with_vars(..., view(*comb_ptr))` on `self_sub` applies the callee's substitution slice a **second time** to the already-substituted type. When the caller is itself inside a generic `impl` or `fn`, any caller `TY_PARAM` substituted in pass 1 whose `param_index < comb_ptr.count` is re-substituted in pass 2 through the callee's `comb_ptr`!
  - Example 1 (reproduced in `tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax:49`): inside `impl<X, Y> Caller<X, Y>`, calling `sy.mix_where<X>(p1.0, |b: X, a: Y| -> (X, Y) { (b, a) })` on `sy: S<Y>` where `impl<A> S<A> { pub fn mix_where<B, F>(self: S<A>, b: B, f: F) -> (B, A) where F: FnOnce<B, A, (B, A)> }`:
    - `comb_ptr = [Y (param 1), X (param 0), ?F]`.
    - Pass 1 (`subst_ty_self`): `fn(S<param 0>, param 1, param 2) -> (param 1, param 0)` becomes `fn(S<Y (1)>, X (0), ?F) -> (X (0), Y (1))`.
    - Pass 2 (`subst_ty_with_vars`): `Y (1)` is re-substituted to `X (0)` and `X (0)` to `Y (1)`, turning `sub_fn` back into `fn(S<X>, Y, ?F) -> (Y, X)`!
  - Example 2: even calling `W<Y>.mk(|| -> Y { ... })` (the exact `T423d` `impl<R> W<R> { fn mk<F: FnOnce<R>> }` signature) from inside `impl<X, Y> Caller<X, Y>` has `comb_ptr = [Y (param 1), ?F]`, so pass 1 yields `W<param 1>` and pass 2 re-substitutes `param 1` to `?F` (the closure type)!
- **Expected:** `qa_cross_impl_and_mixed_generics.ax` compiles and passes in `interp`, `native`, and `native-O1` with stdout `107 205 73 94\n` and exit `42`.
- **Actual:** Compilation fails with two spurious `AX_TYPE_MISMATCH` errors on line 49 (`sy` and `p1.0`):
  ```
  error[AX_TYPE_MISMATCH]: expression type differs from the expected type
   --> tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax:49:26
  error[AX_TYPE_MISMATCH]: expression type differs from the expected type
   --> tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax:49:42
  ```
- **Repro:** `cd build-snap-T423d && python tools/axtest.py --compiler build/axiomc2.exe --filter run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax --no-cache -j 2 --verbose`
- **Suggested fix:** Pass an empty `GenericArgsSlice { args: 0 as *mut TypeId, count: 0 }` to `subst_ty_self` (lines 9279, 9303, 9308) so `subst_ty_self` replaces only `Self` (`MONO_SELF_PARAM_INDEX`), leaving `TY_PARAM` substitution + `TY_VAR` resolution to the single `subst_ty_with_vars` call. (Also check whether `base_ty` itself can contain caller `TY_PARAM`s that would then be substituted by `subst_ty_with_vars` if `Self` is substituted first: if so, substitute `TY_PARAM`s with `subst_ty_with_vars` *first* — which leaves `TC_SELF_PARAM_INDEX` / `MONO_SELF_PARAM_INDEX` intact since `idx < args.count` is false for `0xFFFFFFFF` — and *then* replace `Self` with `subst_ty_self(..., no_args, base_ty.v)`!)

### Checks performed
1. **Build & fixed point (`build-snap-T423d/`):**
   - `python tools/build_axiomc.py --out build --root . --stage 2` -> `STAGE1 OK`, `STAGE2 (O1) OK`, `BUILD-AXIOMC OK` (`size=9372160 sha256=164020a33c504235e5c1265d7cb6062a7176cd4f62a8c629c75400a4807ce431`).
2. **Bundle generators (`build-snap-T423d/`):**
   - `python tests/std/fiber/gen_tests.py --check` -> `OK fiber bundles match live std/fiber`
   - `python tests/conformance/p11/e11_5_executors/gen_tests.py --check` -> `OK e11_5 executor bundles match live std/async and std/fiber`
   - `python tests/perf/p11_executor/gen_tests.py --check` -> `OK p11 executor perf bundles match live std/async and std/fiber`
3. **Native-evidence mutation spot-proof (`build-snap-T423d/` only):**
   - Mutated `// stdout: 7\n` -> `// stdout: 999\n` in `build-snap-T423d/tests/std/fiber/impl_generic_in_method_bound_xfail.ax`, ran `python tools/axtest.py --compiler build/axiomc2.exe --filter std/fiber/impl_generic_in_method_bound_xfail.ax --no-cache -j 2 --verbose` -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all caught stdout byte 0 mismatch).
   - Restored `// stdout: 7\n` -> `TOTAL 3 PASS 3 FAIL 0`, `WEAK-NATIVE 0`.
4. **QA adversarial UI test (`tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax`):**
   - Tests reordered `impl<A, B> Flipped<B, A>` rejecting swapped closure param types, `impl<R> Runner<R> { fn drive<F: Future<Output = R>> }` rejecting mismatched `Future.Output`, `impl<T> Sink<T> for Bucket<T> { fn accept<U: IntoVal<T>> }` rejecting mismatched `IntoVal` arg, and unknown bound name called twice reporting `AX_NAME_UNRESOLVED` once at declaration span.
   - `python tools/axtest.py --compiler build/axiomc2.exe --filter ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax --no-cache -j 2 --verbose` -> `TOTAL 1 PASS 1 FAIL 0`.
5. **Per-task gate (`build-snap-T423d/`):**
   - Command: `python tools/taskgate.py --task T423d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423d.json`
   - Result: `TASKGATE T423d exit=1` — `TOTAL 713 PASS 705 FAIL 3 SKIP 5 XFAIL 0`
   - Parts: `own` 21 (18 PASS / 3 FAIL), `affected` 660 (652 PASS / 3 FAIL / 5 SKIP), `smoke` 55 (55 PASS / 0 FAIL)
   - Failing ids: `run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax` (`interp`, `native`, `native-O1` — F1 above); all other 705 results PASS
   - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
   - `smoke-check (tests/smoke.list): OK; est. worst-case draw 19 s`
   - `Cache: CACHED 41, miss 24, uncacheable 240, stored 21, dep_source exact, verification sample seed=257333823 n=20 of 53 hits, mismatch none`
6. **Task hygiene:**
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423d` (verified after writing this report)
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`

## Files changed
- tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax
- tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax

VERDICT: FAIL round=0

## Round 1

### Summary
Re-gated `T423d` after engineer fix round 1 (`_workspaces/reports/T423d-report.md`, `STATUS: COMPLETE round=1`) inside refreshed snapshot `build-snap-T423d/` (HEAD `2e50e70` + 47 changed files + 60 regenerated selfhost bundles).

Round 0 Finding **F1 is completely fixed**:
- Audited `tc_type_has_self_param`, `tc_deep_resolve_vars`, `tc_subst_ty_and_self`, all 8 `check_expr_method_call` substitution branches, and all 4 bound-helper call sites (`check_future_bound_outputs_for_call`, `tc_callable_bound_to_subst_fn_ty`, `tc_check_single_generic_trait_bound`) in `compiler/types/typeck.ax`, plus `subst_type_with_vars` in `compiler/types/types.ax`.
- Confirmed **zero** remaining `subst_ty_self` + `subst_ty_with_vars` double-substitution pairs anywhere in `compiler/types/typeck.ax` (the only two `subst_ty_self` calls are inside `tc_subst_ty_and_self`).
- Confirmed `tc_subst_ty_and_self` substitutes callee `TY_PARAM`s first via `subst_ty_with_vars`, then `Self` via `subst_ty_self(..., no_args, self_v)` only when `ty` mentions `TC_SELF_PARAM_INDEX` (with the simultaneous single-pass `subst_ty_self` fallback when both `ty` and `args` mention `TC_SELF_PARAM_INDEX`), followed by `tc_deep_resolve_vars` (`args = [0u32]`, which resolves nested `TY_VAR`s without substituting `TY_PARAM(0)`).
- Confirmed QA's Round 0 repro `tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax` was **not weakened** and passes 3/3 (`interp`, `native`, `native-O1`), alongside the engineer's new regression `caller_impl_assoc_and_self_params.ax` (3/3), `std/fiber/impl_generic_in_method_bound_xfail.ax` (3/3), and QA's new Round 1 boundary test `qa_caller_generic_bounds_reject.ax` (1/1).

### Findings
None.

### Checks performed
1. **Build & fixed point (`build-snap-T423d/`):**
   - `python tools/build_axiomc.py --out build --root . --stage 2` -> `STAGE1 OK` (`sha256=19ceb4040eba9edb`), `STAGE2 (O1) OK`, `BUILD-AXIOMC OK` (`size=8381952 sha256=d5af7ab9c409fc479546a3c5bd373778f13de57e8a46b0a9fcfb6c74b8a63b68`, matching Round 1 report fixed-point `axiomc2_O1 == axiomc3_O1`).
2. **Fiber bundle generators (`build-snap-T423d/`):**
   - `python tests/std/fiber/gen_tests.py --check` -> `OK fiber bundles match live std/fiber`
   - `python tests/conformance/p11/e11_5_executors/gen_tests.py --check` -> `OK e11_5 executor bundles match live std/async and std/fiber`
   - `python tests/perf/p11_executor/gen_tests.py --check` -> `OK p11 executor perf bundles match live std/async and std/fiber`
3. **Round 1 QA adversarial boundary test (`tests/ui/impl_generic_in_method_bound/qa_caller_generic_bounds_reject.ax`):**
   - Probes `tc_subst_ty_and_self` inside `impl<X, Y> Caller<X, Y>`: (1) `W<Y>.mk(|| -> X { xv })` rejecting mismatched closure result type `X` vs `Y`; (2) generic trait impl method `CombineSelf<R>.combine_self<F: FnOnce<view<Self>, R, R>>` on swapped `Pair<Y, X>` rejecting mismatched `R` parameter; (3) `TY_PARAM` receiver `u: U` (`U: CombineSelf<Y>`) rejecting mismatched `view<Self>` parameter.
   - `python tools/axtest.py --compiler build/axiomc2.exe --filter impl_generic_in_method_bound --no-cache -j 2 --verbose` -> `TOTAL 25 PASS 25 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (incl. `qa_cross_impl_and_mixed_generics.ax` 3/3, `caller_impl_assoc_and_self_params.ax` 3/3, `qa_adversarial_bounds_reject.ax` 1/1, `qa_caller_generic_bounds_reject.ax` 1/1, `std/fiber/impl_generic_in_method_bound_xfail.ax` 3/3).
4. **Native-evidence mutation spot-proof (`build-snap-T423d/` only):**
   - Mutated `// stdout: 107 205 73 94\n` -> `// stdout: 999 205 73 94\n` in `build-snap-T423d/tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax`, ran `python tools/axtest.py --compiler build/axiomc2.exe --filter run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax --no-cache -j 2 --verbose` -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all caught stdout byte 0 mismatch).
   - Restored -> `TOTAL 3 PASS 3 FAIL 0`, `WEAK-NATIVE 0`.
5. **Per-task gate (`build-snap-T423d/`):**
   - Command: `python tools/taskgate.py --task T423d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423d.json`
   - Result: `TASKGATE T423d exit=0` — `TOTAL 723 PASS 715 FAIL 0 SKIP 5 XFAIL 3` (wall time 1468.7 s)
   - Parts: `own` 58 ids / 157 results (154 PASS / 0 FAIL / 3 XFAIL), `affected` 289 ids / 664 results (659 PASS / 0 FAIL / 5 SKIP), `smoke` 33 ids / 56 results (56 PASS / 0 FAIL); total dedup 323 ids across 30 groups (`conformance`, `driver`, `mir`, `modules`, `perf`, `run`, `selfhost`, `std`, `typeck`, `ui`, plus smoke groups).
   - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`
   - `Baseline: BASELINE OK`; `Failing ids: none`
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
   - `smoke-check (tests/smoke.list): OK; est. worst-case draw 20 s`
   - `Cache: CACHED 52, miss 17, uncacheable 244, stored 14, dep_source exact, verification sample seed=890309371 n=20 of 62 hits, mismatch none, rejected {}, producer snapshot`
6. **Task hygiene:**
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423d` -> 0 `REFUSED` lines (47 staged files incl. all 3 QA tests).
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

## Files changed
- tests/run/impl_generic_in_method_bound/qa_cross_impl_and_mixed_generics.ax
- tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax
- tests/ui/impl_generic_in_method_bound/qa_caller_generic_bounds_reject.ax

VERDICT: PASS round=1

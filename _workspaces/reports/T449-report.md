# T449 report

## Summary
The concurrency spawn checks (`Send`/`Share`/escaping-view) are now keyed on the spawn contract, not on the callee spelling `spawn`:
- A call is a spawn boundary only if its resolved definition is a designated spawn entry point:
  - A function or method carrying `@lang("spawn")` / `@lang("spawn_blocking")` / `@lang("spawn_local")` / `@lang("spawn_scoped")` (or direct `@spawn` / `@spawn_blocking` / `@spawn_local` / `@spawn_scoped` attributes).
  - A 1-arg free function named `spawn` / `spawn_blocking` / `spawn_local` / `spawn_scoped` whose defining `module_path` starts with `std` (e.g. `std.thread.spawn`, incl. `use` aliases), or—solely for compatibility with the unchanged legacy stubs in `tests/ui/concurrency/{spawn_capture,data_race,tls}/*`—a non-`std` 1-arg generic free function of that name whose generic parameter or `where` clause carries a `FnOnce` bound.
  - A `spawn`-family method on a `std.*` receiver struct (`Executor`, `LocalExecutor`, `Builder`) or on `Scope` (kept compatible with the 3 unchanged `tests/ui/concurrency/data_race/*` stubs).
  - User methods or free functions merely named `spawn` (including `struct Executor` in a non-`std` module and `fn spawn<T: MyTag>(x: T)` without `@lang` or `FnOnce`) are NOT checked (`compiler/types/typeck.ax`: `tc_item_spawn_attr_kind`, `tc_receiver_spawn_method_kind`, `tc_def_is_free_spawn_fn`, `classify_spawn_call`; `compiler/own/unsafe.ax`: `conc_resolve_call_def`, `conc_item_spawn_attr_kind`, `conc_def_is_free_spawn_fn`, `conc_classify_spawn_call`).
- Generic by-value arguments are checked against `Send` (not `Share`) after substitution; bounds in `where` clauses and generic struct field substitution are honoured (`conc_type_satisfies_auto`).
- `view` arguments of non-spawn calls no longer produce `AX_CONC_ESCAPING_VIEW`; raw-pointer locals passed through nested calls in arguments of non-spawn calls no longer produce `AX_CONC_VIEW_NOT_SHARE`; raw pointers (`TY_PTR`) resolve to their pointee def name for negative-impl lookup.
- Round-0 fix found by the gate: `conc_resolve_call_def` forged a `*const HirExpr` from the integer `expr_methods` symbol-index key (`(sym << 3) | 4`), which the MIR interpreter rejects (`AX_UNSAFE_INTERP_UB`, failing `selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax` and `selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax` in interp mode). Now uses `ptr_itemmap_get` with a `usize` key, like typeck/mir builder.

## Files changed
- compiler/own/unsafe.ax
- compiler/types/typeck.ax
- tests/ui/concurrency/spawn_contract/generic_by_value_send_ok.ax
- tests/ui/concurrency/spawn_contract/std_thread_spawn_non_send_reject.ax
- tests/ui/concurrency/spawn_contract/user_method_spawn_ok.ax
- _workspaces/reports/T449-report.md

## Tests
All in `build-snap-T449` (HEAD a3d2292 + T449 change set), stage-3 axiomc (fixed point O1 OK, sha256 e7665097…):
- `axtest ui/concurrency`: TOTAL 32 PASS 32 FAIL 0 (incl. the 3 new `spawn_contract` tests; existing `data_race/*` expectations unchanged).
- `taskgate.py --task T449 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`: axtest TOTAL 327 PASS 326 FAIL 0 SKIP 1; BASELINE OK; archcheck clean; `TASKGATE T449 exit=0`.
- `taskctl changes T449`: 0 REFUSED.

## Spec deviations
- SPEC-30/34 name no concrete marking mechanism for spawn entry points. Chosen: `@lang("spawn")` / `@lang("spawn_blocking")` / `@lang("spawn_local")` / `@lang("spawn_scoped")` attribute on a declaration designates a spawn entry point; additionally the std entry points are recognised by their resolved definition (`module_path` starting with `std` for free fns and `Executor`/`LocalExecutor`/`Builder` methods, plus legacy stub compatibility for `Scope` and non-`std` `FnOnce`-bounded `spawn`/`spawn_local`/`spawn_scoped` stubs; no `std/` edit made). Architect to confirm or replace the path recognition by `@lang` on the std declarations.

## Follow-ups
- Add `@lang("spawn")` / `@lang("spawn_local")` / `@lang("spawn_scoped")` / `@lang("spawn_blocking")` to the std spawn declarations (std/ out of scope here) and retire the receiver-type-name and legacy-stub fallbacks.

## Round 1

Addressed all 3 QA Round-0 findings (`_workspaces/reports/T449-qa.md`) and verified `tests/ui/concurrency/spawn_contract/qa_spawn_contract_adversarial.ax` passes without modification:

1. **FINDING-1 (`compiler/types/typeck.ax`, `compiler/own/unsafe.ax`)**:
   - Updated `tc_item_spawn_attr_kind` in `compiler/types/typeck.ax` to recognize `sv_is_spawn_blocking_name(...)` (for `@lang("spawn_blocking")`, `@lang(spawn_blocking)`, and direct `@spawn_blocking`) returning `1u8` (unscoped spawn boundary — requires `Send` and rejects escaping `view<T>`, emitting `AX_CONC_CAPTURE_NOT_SEND` / `AX_CONC_ESCAPING_VIEW` instead of skipping spawn checks or falling through to generic `AX_CONC_NOT_SEND`). Added matching direct `@spawn_blocking` check in `conc_item_spawn_attr_kind` and free-fn `spawn_blocking` support in `tc_def_is_free_spawn_fn`.
2. **FINDING-2 (`compiler/types/typeck.ax`, `compiler/own/unsafe.ax`)**:
   - Added `tc_item_is_std_module` (in `compiler/types/typeck.ax`) and `conc_item_is_std_module` + `conc_type_def_item` (in `compiler/own/unsafe.ax`) checking that `(*sdef).module_path` starts with `"std"`.
   - Gated the `Executor` / `Builder` / `LocalExecutor` receiver-type fallback in both `tc_receiver_spawn_method_kind` and `conc_classify_spawn_call` on `std.*` module membership, while leaving `Scope` compatible with the 3 unchanged `tests/ui/concurrency/data_race/*` stubs. User `struct Executor` in `module main` is no longer checked as a spawn boundary.
3. **FINDING-3 (`compiler/types/typeck.ax`, `compiler/own/unsafe.ax`)**:
   - Added `sv_is_fnonce_name` / `tc_bound_is_fnonce` / `tc_item_has_fnonce_bound` (in `compiler/types/typeck.ax`) and `conc_sv_is_fnonce_name` / `conc_bound_is_fnonce` / `conc_item_has_fnonce_bound` (in `compiler/own/unsafe.ax`).
   - Updated `tc_def_is_free_spawn_fn` and `conc_def_is_free_spawn_fn` to check `module_path` starting with `"std"` first, and to require an `FnOnce` bound on the generic parameter / `where` clause for the non-`std` legacy-stub fallback. User free functions like `fn spawn<T: MyTag>(x: T)` in `module main` are no longer misclassified.

### Round 1 verification (`build-snap-T449`, HEAD `39e6a4d44a27` + T449 change set)
- Stage-3 build (`python tools/build_axiomc.py --out build --stage 3`): exit 0; `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == f79d69c43fdb46aa43772e743e081de42078af10a1dd4d298b75fe4b39426cbb` (8356352 bytes).
- `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter ui/concurrency`: `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0` (exit 0; includes `qa_spawn_contract_adversarial.ax`, `qa_spawn_alias_and_nested_ptr.ax`, the 3 T449 `spawn_contract/*` tests, and all unchanged `data_race/*`, `spawn_capture/*`, `tls/*`, `atomics/*`, `send_share/*` tests).
- `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter ui/async/send_bounds`: `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (exit 0).
- `python tools/taskgate.py --task T449 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`: `TOTAL 328 PASS 327 FAIL 0 SKIP 1 XFAIL 0`; `BASELINE OK`; `archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations`; `TASKGATE T449 exit=0`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T449`: exit 0, 0 `REFUSED` lines.

STATUS: COMPLETE round=1

# T423c report

## Tóm tắt

Đã chẩn đoán và sửa triệt để lỗi suy diễn tham số kiểu hàm tổng quát (generic type-argument inference) bên trong thân closure (`AX_TYPE_UNKNOWN` khi gọi `g(1i64)` trong `|| -> i64 { .. }`), đồng thời hoàn thiện truyền kiểu sau hợp nhất và đơn hình hóa (monomorphization) closure nằm trong hàm/impl tổng quát trên cả 3 chế độ `interp`, `native`, và `native-O1`. Gỡ `xfail` khỏi `tests/std/fiber/closure_generic_infer_xfail.ax`, bổ sung đủ 9 kịch bản kiểm thử tại `tests/run/closure_generic_infer/*.ax` (`28/28 PASS`, `WEAK-NATIVE 0`), xác minh điểm bất động `axiomc2 == axiomc3` (`FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`) và vượt qua `taskgate.py` (`494/496 PASS`, `0 FAIL`, `2 SKIP`).

## Summary

### Root Causes Fixed

1. **Orphaned generic `TY_VAR`s during closure capture pre-scan (`compiler/types/typeck.ax`):**
   - `scan_expr_captures` previously called `lookup_path_type` on every `HIR_EXPR_CALL` callee inside a closure body solely to detect prelude `drop` (`TY_BUILTIN_DROP`) so its argument would be marked `CAP_MOVE`.
   - When the callee was a generic function called without explicit `<TypeArgs>`, `lookup_path_type -> instantiate_path` allocated fresh `TY_VAR` entries (`is_generic = true`) in `cx.type_vars` that `scan_expr_captures` immediately discarded without unifying against call arguments or return context. At the end of checking the enclosing function, `default_int_vars` saw those unconstrained `is_generic` type variables and emitted `AX_TYPE_UNKNOWN` at the callee span.
   - Replaced `lookup_path_type` in `scan_expr_captures` with read-only `tc_is_builtin_drop_callee`, checking whether the callee resolves to the prelude `drop` symbol (`TY_BUILTIN_DROP`) without instantiating generic paths or mutating `cx.type_vars`.

2. **Post-closure `TY_VAR` unification into `TY_CLOSURE` and synthetic `fn_item` (`compiler/types/typeck.ax`):**
   - When a generic call inside a closure inferred `T` from expected return type or parameter type unified *after* `check_expr_closure` returned (for example `let r: i64 = apply_once(|| make_seeded(13i64))` or `apply_after(|v| id(v), 120i64)`), `finalize_types` previously resolved `TY_CLOSURE.captures` in place but left `TY_CLOSURE.param_types`, `TY_CLOSURE.ret_type`, `TY_CLOSURE.fn_type`, and the synthetic closure `fn_item`'s `item_types`/`param_types`/`symbol_types` pointing at raw `TY_VAR`s.
   - Extended `finalize_types` (`k == TY_CLOSURE`) to deep-resolve `param_types` and `ret_type`, rebuild `fn_type` when updated, and synchronize the synthetic `fn_item` recorded in `(*t).def`.

3. **Monomorphization of closures inside generic functions/impls calling generic functions with outer `T` (`compiler/types/typeck.ax`, `compiler/traits/mono.ax`, `compiler/mir/builder.ax`):**
   - Synthetic closure `fn_item`s have `generic_params = 0` (preserving `.thir` dump format parity with `axiom0`). In `finish_closure_item`, attached the enclosing impl + function `TY_PARAM` list onto `TY_CLOSURE.args`/`arg_count` and tagged the synthetic `fn_item` with its enclosing generic function/impl in `thir.expr_methods` / `thir.item_types`.
   - Updated `type_contains_param`, `subst_ty_enum_or_closure` (with collision-safe `closure_id` lookup in `TypeInterner.map`), and `deduce_args` in `compiler/traits/mono.ax` to propagate, substitute, and deduce `TY_CLOSURE` generic arguments.
   - Added `mb_bind_closure_mono_in_ty` (invoked from `mb_resolve_ty`) and updated `mb_count_generic_params_in_hir` + `mb_mono_find_or_create` in `compiler/mir/builder.ax` so concrete instantiations of closures inside generic items clone a monomorphized `HirItem` with a fresh `mangled_sym`, register it in `thir.expr_methods`, and clone + substitute `(*new_it).params` in `thir.param_types` (ensuring `--interp`'s `prepare_call_args_from_term` copies multi-word captured structs like 16-byte `Pair16` at their full concrete size rather than falling back to 8 bytes on `TY_PARAM`).

## Files changed

- compiler/types/typeck.ax
- compiler/traits/mono.ax
- compiler/mir/builder.ax
- tests/std/fiber/closure_generic_infer_xfail.ax
- tests/run/closure_generic_infer/ambiguous_call_ui.ax
- tests/run/closure_generic_infer/closure_in_generic_fn.ax
- tests/run/closure_generic_infer/higher_order_generic_fn.ax
- tests/run/closure_generic_infer/infer_from_arg.ax
- tests/run/closure_generic_infer/infer_from_return_type.ax
- tests/run/closure_generic_infer/method_generic_call.ax
- tests/run/closure_generic_infer/move_closure.ax
- tests/run/closure_generic_infer/multi_type_calls.ax
- tests/run/closure_generic_infer/nested_closures.ax

## Tests

All builds and tests were executed inside isolated snapshot worktree `build-snap-T423c/` (`-j 2`):

- **Stage-2/3 fixed-point build (`python tools/build_axiomc.py --out build --root . --stage 2`):**
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 464321a6cf51dda9fbc9b424e51b00decc80a11f59ac848a9f643269fa0a8b0f` (`8,686,080` bytes).
  - `STAGE0-GUARD OK`: `axiomc1` and stage-2 produced byte-identical `.exe` on all 6 smoke programs (including `Xin chào thế giới`).
- **Targeted T423c suite (`python tools/axtest.py --compiler build/axiomc2.exe --filter run/closure_generic_infer --filter std/fiber/closure_generic_infer_xfail.ax --no-cache -j 2 --verbose`):**
  - `TOTAL 28 PASS 28 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - Covers: (1) `infer_from_arg.ax`, (2) `infer_from_return_type.ax`, (3) `multi_type_calls.ax`, (4) `nested_closures.ax`, (5) `closure_in_generic_fn.ax`, (6) `move_closure.ax` (inferred `CAP_MOVE` on non-`Copy` `Drop` value with deterministic drop-order verification), (7) `higher_order_generic_fn.ax`, (8) `method_generic_call.ax`, (9) `ambiguous_call_ui.ax` (`AX_TYPE_UNKNOWN` at exact span `[229..236]`), plus un-xfailed `tests/std/fiber/closure_generic_infer_xfail.ax`.
- **Native-evidence mutation spot-proof (inside `build-snap-T423c/` only):**
  - Temporarily mutated `// stdout: 42 9 300 77 150\n` to `// stdout: 42 9 999 77 150\n` in `build-snap-T423c/tests/run/closure_generic_infer/closure_in_generic_fn.ax` and ran `axtest.py --no-cache`: confirmed `[interp]`, `[native]`, and `[native-O1]` all failed (`TOTAL 3 PASS 0 FAIL 3`). Restored byte-identical (`sha256=d3aef5ea820f49ac5d200e111593917fde39e79477969ddf8d695e274e93f3cf`) and re-verified `TOTAL 3 PASS 3 FAIL 0`.
- **Per-task gate (`python tools/taskgate.py --task T423c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):**
  - `own`: `10 ids, 28 PASS, 0 FAIL` (`WEAK-NATIVE: 0 in the task's own/changed tests`)
  - `affected` (including 40 `selfhost` tests across `typeck`, `traits`, `mir`, `interp`, `backend`, `driver`, `verify`, `drop`, `lir`, `opt`): `242 ids, 445 PASS, 0 FAIL, 2 SKIP`
  - `smoke`: `32 ids, 53 PASS, 0 FAIL`
  - **Dedup total:** `TOTAL 496 PASS 494 FAIL 0 SKIP 2 XFAIL 0` (`TASKGATE T423c exit=0`, `BASELINE OK`, `archcheck: 232 files scanned, 0 violations`).

## Spec deviations

none

## Follow-ups

- Optional cleanup in `std/fiber/mod.ax` (outside `T423c`'s `paths:`): internal closures that previously used explicit turbofish arguments (`yield_val<T>(x)`) as a workaround for `T423c` can omit explicit `<T>` if desired.

STATUS: COMPLETE round=0

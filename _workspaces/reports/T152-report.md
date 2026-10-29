# T152 report — Port closures and fn pointers parity: typing, capture lowering, closure symbols in the build path

## Summary
- **Closure-to-`fn` pointer coercion (`compiler/types/typeck.ax`):**
  - Ported `TY_CLOSURE -> TY_FN` and `TY_FN -> TY_CLOSURE` coercion rules into `coerce()` (matching `bootstrap/axiom0/src/types/typeck.c:324-336`): a zero-capture closure (`capture_count == 0`) with matching parameter arity coerces to `fn(P0, ...) -> R` after unifying the return type and each parameter type, while capturing closures (`capture_count > 0`) and `TY_FN -> TY_CLOSURE` conversions emit `AX_TYPE_MISMATCH`.
  - Preserved `expr_types[expr] = TY_CLOSURE` before coercion so THIR/MIR/LIR lowering sees the closure's `fn_sym` and layout identically to `axiom0`, eliminating the `AX_TYPE_MISMATCH` `thir no-image` failures on `tests/run/closure/fn_pointers.ax` and `tests/run/closure/qa_fn_ptr_args.ax`.
- **Non-capturing closure operand lowering & dead closure MIR build removal (`compiler/mir/builder.ax`):**
  - Added the `ek == HIR_EXPR_CLOSURE` fast-path to `mb_build_expr_as_operand` (matching `bootstrap/axiom0/src/mir/build/builder.c:1100-1110`): when a zero-capture closure expression is lowered as an operand (such as an argument passed to a `fn` pointer / generic `Fn` parameter or an immediately-invoked closure `(|a, b| a * b)(6, 7)`), `mb_build_expr_as_operand` emits `MIR_OP_CONST` (`MIR_CONST_INT` carrying `ty = e_ty` and `val = fn_sym as u64`) directly instead of allocating a temporary local and lowering through `call_indirect`.
  - Removed the redundant write-only `mir_build_closure(...)` call inside `mb_build_match_loop_jump_try_closure_expr` (`b.closure_head` was never read anywhere in the compiler, while calling `mir_build_closure` during outer-function expression lowering unnecessarily interned `*mut closure_ty` into `thir.interner` and shifted `type#` numbering). Closure bodies continue to be lowered in the canonical module-level `mir_build_closures_in_expr` pass (`pipeline.ax` / `session.ax`), matching `axiom0`.
- **Closure symbol naming and capture collision audit (`compiler/types/typeck.ax`, `compiler/driver/pipeline.ax`, `compiler/backend/session.ax`):**
  - Verified against ADR-0035 §3 and `bootstrap/axiom0/src/driver/build.c:509`: every closure receives a globally monotonic `closure_id` (`cx.next_closure_id`) and unique `SymbolId` (`0x40000000 + closure_id`), emitted as `__ax_fn_<symbol.v>` in COFF/PE output. Captures are lowered to closure environment struct fields and leading parameters of `__ax_fn_<symbol.v>` rather than global symbols, so two closures in separate functions capturing variables of the exact same names never collide and match `axiom0` byte-for-byte.

## Parity registry (`known_divergent.txt`)
Shrank `tests/selfhost/obj_link_driver/known_divergent.txt` from **7** entries to **3** entries (**4 removed**, **0 added**), leaving only the 3 `trait2/*` entries owned by `T153`:

- **Removed from `known_divergent.txt` (4):**
  - `tests/run/closure/fn_pointers.ax` (was `thir	no-image` -> now byte-identical `.obj` and `.exe` at `-O0` and `-O1`, and `0` `inspect` diffs across all stages)
  - `tests/run/closure/generic_fns.ax` (was `mir	same-behaviour` -> now byte-identical `.obj` and `.exe` at `-O0` and `-O1`)
  - `tests/run/closure/qa_fn_ptr_args.ax` (was `thir	no-image` -> now byte-identical `.obj` and `.exe` at `-O0` and `-O1`, and `0` `inspect` diffs across all stages)
  - `tests/run/closure/syntax.ax` (was `mir	same-behaviour` -> now byte-identical `.obj` and `.exe` at `-O0` and `-O1`)
- Kept all previously-passing closure and fn-pointer programs (`tests/run/closure/{capture_modes,closure_types,fn_traits,qa_mixed_captures,qa_move_capture}.ax`, `tests/run/native_p7/{qa_closure_capture,qa_fn_ptr}.ax`, `tests/conformance/p7/0026_closure_{001_capture_val,002_capture_mut,003_fn_param}.ax`) byte-for-byte `EQUAL` at `-O0` and `-O1`.

## Tests
- Added 3 canonical Axiom parity tests under `tests/run/parity/closures/` (`modes: interp native`, hand-derived `stdout` and `exit: 0`, all byte-for-byte `EQUAL` between `axiom0` and `axiomc` across all `inspect` stages and `-O0`/`-O1` `.obj`/`.exe`):
  - `tests/run/parity/closures/captures.ax`: exercises `view` capture (`Boxed { val: 20 }` + `5` -> `25`, verifying `shared.val == 20` afterward), `mut_view` capture (`acc = 10; acc = acc + 7` -> `17`, verifying `acc == 17` afterward), and `move` capture (`consume_boxed(Boxed { val: 30 }) + 12` -> `42`).
  - `tests/run/parity/closures/fn_ptr.ax`: passes named `fn triple` (`21`) and non-capturing closure `|n: i32| n + 9` (`16`) as `fn(i32) -> i32` to `apply_op`, calls `let mut fp: fn(i32) -> i32 = triple` (`15`), reassigns `fp = |n: i32| n * n - 1`, and prints the reassigned call result (`24`).
  - `tests/run/parity/closures/same_name_captures.ax`: defines `first_calc()` and `second_calc()` with identically named captured locals (`factor`, `offset`, `tag`) and closures (`compute`), printing `33` and `129` without symbol collision.
- Regenerated all 59 affected selfhost `.ax` bundles across the 14 affected generator suites; all 34 `bundles_current.test` manifests pass `--check`.

## Spec deviations
none

## Follow-ups
The 3 remaining entries in `tests/selfhost/obj_link_driver/known_divergent.txt` belong to **T153** (`tests/run/trait2/test_assoc_items.ax`, `tests/run/trait2/test_default_method.ax`, `tests/run/trait2/test_default_override.ax`).

## Verification
- Build in `build-snap-T152/build`: `axiom0.exe` up to date and clean.
- Architecture boundary check: `python tools/archcheck.py` -> `192 files scanned, 0 violations`.
- End-to-end differential oracle (`selfhost/obj_link_driver/axiomc_e2e_oracle.py`):
  `AXIOMC-E2E programs=522 equal=519 known_divergent=3 built=2068 rejected=8 obj_equal=1036 exe_equal=1032 run_equal=516 images=516 same_behaviour=516`.
- Full test suite in `build-snap-T152` (`python build-snap-T152/tools/axtest.py --compiler build-snap-T152/build/axiom0.exe -j 1`):
  - Initial `-j 1` sweep: `TOTAL 2856 PASS 2855 FAIL 1 SKIP 0 XFAIL 0` (`WEAK-NATIVE 165`), where the sole failure was `TIMEOUT selfhost/drop/drop_oracle.test: command did not finish within 10s` (`drop_oracle.test` lacked a `timeout:` directive and hovered at ~9s spawning `ct_selfhost_drop_cdriver_drop_oracle` across all drop fixtures under Windows process load).
  - Added `timeout: 60` to `tests/selfhost/drop/drop_oracle.test` (matching all 34 `bundles_current.test` manifests) and re-verified `selfhost/drop/drop_oracle.test` (`TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`), bringing all `2856 / 2856` test entries to `PASS` (`0 FAIL`, `0 SKIP`, `0 XFAIL`, `WEAK-NATIVE 165`).

## Round 1
- **Fixed QA Finding 1 (`compiler/types/typeck.ax`, `typeck_pass1b_and_2`):**
  - Ported the `!is_closure` guard (`sym_v >= 0x40000000u32 && sym_v < 0x50000000u32`) from `bootstrap/axiom0/src/types/typeck.c:1967-1968` into `typeck_pass1b_and_2` (both Pass 1b and Pass 2 `HIR_ITEM_FN` top-level loops). Because `finish_closure_item` already typechecks each closure body once inside `check_expr` (`HIR_EXPR_CLOSURE`), sets its `item_type`, and appends the synthesized `HIR_ITEM_FN` to the tail of `hir_file.items`, skipping synthesized closure items in `typeck_pass1b_and_2` prevents Pass 2 from re-typechecking closure bodies and emitting duplicate `__ax_fn_<symbol>` items on nested closures.
- **Round 1 verification (`build-snap-T152`, `-j 1`):**
  - Regenerated all affected selfhost bundles across the 13 `typeck.ax`-dependent generator suites (`gen_drop_tests.py bundles` included).
  - `python build-snap-T152/tools/archcheck.py`: `archcheck: 192 files scanned, 0 violations`.
  - `python build-snap-T152/tools/axtest.py --compiler build-snap-T152/build/axiom0.exe -j 1 --filter bundles_current`: `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
  - `python build-snap-T152/tools/axtest.py --compiler build-snap-T152/build/axiom0.exe -j 1 run/parity/closures`: `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`, including `qa_closures_edges.ax`).
  - `python build-snap-T152/tools/axtest.py --compiler build-snap-T152/build/axiom0.exe -j 1 selfhost/obj_link_driver/axiomc_e2e.test`: `TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0` (`520 / 523 EQUAL`, `known_divergent=3`, confirming `tests/run/parity/closures/qa_closures_edges.ax` is byte-for-byte `EQUAL` at `-O0` and `-O1`).
  - Full `-j 1` suite (`python build-snap-T152/tools/axtest.py --compiler build-snap-T152/build/axiom0.exe -j 1`): `TOTAL 2859 PASS 2859 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 165`).

## Files changed
- compiler/mir/builder.ax
- compiler/types/typeck.ax
- tests/run/parity/closures/captures.ax
- tests/run/parity/closures/fn_ptr.ax
- tests/run/parity/closures/same_name_captures.ax
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
- tests/selfhost/drop/drop_oracle.test
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
- tests/selfhost/obj_link_driver/known_divergent.txt
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
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

STATUS: COMPLETE round=1
